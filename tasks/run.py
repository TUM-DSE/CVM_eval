#!/usr/bin/env python3
import os
import time
from typing import Any

import kernel
import utils

from spdk import VHOST_CONTROLLER_NAME

from common import RAMDISK_PATH, info_print, warn_nvm_use, print_and_run, print_and_sudo, err_print, REPO_DIR, VM_BUILD_DIR, warn_print, EVAL_NVME_PATH

from invoke import task
# warning: dependency
from ovmf import OVMF_CODE_NAME, OVMF_RW_DIR, OVMF_VARS_NAME, UEFI_BIOS_CODE_RW_PATH, UEFI_BIOS_VARS_RW_PATH, make_ovmf
from build import IMG_RW_PATH, build_nixos_bechmark_image
from utils import exec_fio_in_vm, ssh_vm, DEFAULT_SSH_FORWARD_PORT, cryptsetup_open_ssd_in_vm, VM_BENCHMARK_SSD_PATH, VM_BENCHMARK_SCSI_PATH, CRYPTSETUP_TARGET_PATH, stop_qemu, await_vm_fio, NVME_VM_BENCHMARK_SSD_PATH
from utils import FIO_VM_JOB_PATH, FIO_QUICK_VM_JOB_PATH

# constants
QEMU_BIN = "qemu-system-x86_64"
DEFAULT_NUM_CPUS = 4
DEFAULT_NUM_MEM_GB = 16
DEFAULT_QMP_SOCKET_PATH = "/tmp/qmp-sock"

ENGINE_VIRTIO_BLK = "virtio-blk"
ENGINE_NVME = "nvme"
STORAGE_ENGINES = [
    ENGINE_VIRTIO_BLK,
    ENGINE_NVME
        ]

benchmark_help={
    'vm_type': "Type of VM to run (default: native; of {native, sev})",
    'num_mem_gb': f"Number of GBs of memory (default: {DEFAULT_NUM_MEM_GB})",
    'num_cpus': f"Number of vCPUs (default: {DEFAULT_NUM_CPUS})",
    'rebuild_image': "Rebuild nixos image (also recompiles kernel- takes a while)",
    'dm_benchmark': "Runs fio on dm devices on top of SSD",
    'stop_qemu_before_benchmark': "Stops QEMU before running benchmark",
    'fio_benchmark': "Which fio benchmark to run. Options: all, alat, bw, iops, <custom>",
    'ignore_warning': "Ignore warning about using NVMe device",
    'await_results': "Wait for fio results to be available and copy to host (takes duration of benchmark, can be called separately)",
    'rebuild_ovmf': "Rebuild OVMF (sometimes necessary if Qemu doesn\'t boot)",
    'benchmark_tag': "Tag for benchmark (used for naming results file)",
    'ssd_path': f"Path to SSD device (default: {EVAL_NVME_PATH})",
    'storage_engine': f"Storage engine to use (default: {ENGINE_VIRTIO_BLK}; of {STORAGE_ENGINES})",
    }


# build artefacts
## OVMF

# invariant to any qemu execution
def build_base_qemu_cmd(
        c: Any,
        ssh_forward_port: int,
        num_mem_gb:int = DEFAULT_NUM_MEM_GB,
        num_cpus: int = DEFAULT_NUM_CPUS,
        qmp_socket_path: str = DEFAULT_QMP_SOCKET_PATH
        ) -> str:
    return f"{QEMU_BIN} " \
        "-cpu EPYC-v4,host-phys-bits=true " \
        "-enable-kvm " \
        f"-smp {num_cpus} " \
        f"-m {num_mem_gb}G " \
        "-nographic " \
        f"-netdev user,id=net0,hostfwd=tcp::{ssh_forward_port}-:22 " \
        "-device virtio-net-pci,netdev=net0 " \
        "-serial null " \
        "-device virtio-serial " \
        "-chardev stdio,mux=on,id=char0,signal=off " \
        "-mon chardev=char0,mode=readline " \
        "-device virtconsole,chardev=char0,id=cvmio,nr=0 " \
        f"-qmp unix:{qmp_socket_path},server=on,wait=off"


def build_benchmark_qemu_cmd(
        c: Any,
        num_mem_gb: int = DEFAULT_NUM_MEM_GB,
        num_cpus: int = DEFAULT_NUM_CPUS,
        rebuild_image: bool = False,
        rebuild_ovmf: bool = False,
        port: int = DEFAULT_SSH_FORWARD_PORT,
        qmp_socket_path: str = DEFAULT_QMP_SOCKET_PATH
        ):
    base_cmd = build_base_qemu_cmd(
            c,
            port,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            qmp_socket_path=qmp_socket_path
            )
    if rebuild_image or not os.path.exists(IMG_RW_PATH):
        build_nixos_bechmark_image(c)

    if rebuild_ovmf or not (os.path.exists(UEFI_BIOS_CODE_RW_PATH) and os.path.exists(UEFI_BIOS_VARS_RW_PATH)):
        make_ovmf(c)
    # no need to rebuild ovmf if already exist
    if not (os.path.exists(UEFI_BIOS_CODE_RW_PATH) and os.path.exists(UEFI_BIOS_VARS_RW_PATH)):
        make_ovmf(c)

    return f"{base_cmd} " \
        f"-blockdev qcow2,node-name=q2,file.driver=file,file.filename={IMG_RW_PATH} " \
        "-device virtio-blk-pci,bootindex=0,drive=q2 "

def add_sev_to_qemu_cmd(
        base_cmd: str,
        ):
    return f"{base_cmd} " \
        "-machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off " \
        "-object memory-backend-memfd-private,id=ram1,size=16G,share=true " \
        "-object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA"

def add_ovmf_to_qemu_cmd(
        base_cmd: str,
        ovmf_dir: str = OVMF_RW_DIR,
        ):
    ovmf_code_path = os.path.join(ovmf_dir, OVMF_CODE_NAME)
    ovmf_vars_path = os.path.join(ovmf_dir, OVMF_VARS_NAME)
    return f"{base_cmd} " \
        f"-drive if=pflash,format=raw,unit=0,file={ovmf_code_path},readonly=on " \
        f"-drive if=pflash,format=raw,unit=1,file={ovmf_vars_path}"

def add_virtio_blk_nvme_to_qemu_cmd(
        base_cmd: str,
        nvme_path: str = EVAL_NVME_PATH,
        ignore_warning: bool = False,
        iothreads: bool = True,
        aio: str = "native", # threads, native, io_uring
        direct: bool = True,
        no_flush: bool = False,
        scsi: bool = False,
        ):

    # QEMU options (https://www.qemu.org/docs/master/system/qemu-manpage.html)
    # -drive cache=
    #
    # |              | cache.writeback | cache.direct | cache.no-flush |
    # |--------------|-----------------|--------------|----------------|
    # | writeback    | on              | off          | off            |
    # | none         | on              | on           | off            |
    # | writethrough | off             | off          | off            |
    # | directsync   | off             | on           | off            |
    # | unsafe       | on              | off          | on             |
    #
    # cache.writeback=on by default

    if not ignore_warning:
        warn_nvm_use(nvme_path)

    if len(aio) > 0 and not iothreads:
        # not implemented
        warn_print("aio is enabled only with iothreads")
    if aio != "threads" and aio != "native" and aio != "io_uring":
        warn_print(f"aio must be either of threads, native, io_uring: {aio}")

    if direct:
        direct_option = "on"
    else:
        direct_option = "off"
        warn_print(f"blockdev cache.direct={direct_option}; use host page-cache")
        if aio == "native":
            warn_print("aio=native requires cache.direct=on")

    if no_flush:
        no_flush_option = "on"
        warn_print(f"blockdev cache.no-flush={direct_option}")
    else:
        no_flush_option = "off"

    if iothreads:
        if len(aio) > 0:
            # iothreads, aio
            if scsi:
                cmd = f"{base_cmd} " \
                    f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},file.aio={aio},cache.direct={direct_option},cache.no-flush={no_flush_option} " \
                    "-device virtio-scsi-pci,id=scsi0,iothread=iothread0 " \
                    "-device scsi-hd,drive=q1 " \
                    "-object iothread,id=iothread0 "
            else:
                cmd = f"{base_cmd} " \
                    f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},file.aio={aio},cache.direct={direct_option},cache.no-flush={no_flush_option} " \
                    "-device virtio-blk,drive=q1,iothread=iothread0 " \
                    "-object iothread,id=iothread0 "
        else:
            # iothreads, no aio
            cmd = f"{base_cmd} " \
                f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},cache.direct={direct_option},cache.no-flush={no_flush_option} " \
                "-device virtio-blk,drive=q1,iothread=iothread0 " \
                "-object iothread,id=iothread0 "
            if scsi:
                raise NotImplementedError
    else:
        # no iothreads, no aio
        cmd = f"{base_cmd} " \
            f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},cache.direct={direct_option},cache.no-flush={no_flush_option} " \
            "-device virtio-blk,drive=q1 "
        if scsi:
            raise NotImplementedError

    return cmd

def add_nvme_to_qemu_cmd(
        base_cmd: str,
        nvme_path: str = EVAL_NVME_PATH,
        ignore_warning: bool = False,
        use_file: bool = False,
        ):

    if not ignore_warning:
        warn_nvm_use(nvme_path)

    if use_file:
        file_driver = "file"
    else:
        file_driver = "host_device"

    return f"{base_cmd} " \
        f"-blockdev node-name=q1,driver=raw,file.driver={file_driver},file.filename={nvme_path} " \
        "-device nvme,drive=q1,serial=deadbeef"


# tasks
@task(help={
    'vm_type': "Type of VM to run (default: native; of {native, sev})",
    'num_mem_gb': "Number of GBs of memory",
    'num_cpus': "Number of CPUs",
    'rebuild_image': "Rebuild nixos image (also recompiles kernel- takes a while)",
    'rebuild_ovmf': "Rebuild OVMF",
    'ssd_path': "Path to NVMe SSD",
    })
def run_virtio_blk_qemu(
        c: Any,
        vm_type: str = "native",
        num_mem_gb: int = DEFAULT_NUM_MEM_GB,
        num_cpus: int = DEFAULT_NUM_CPUS,
        rebuild_image: bool = False,
        rebuild_ovmf: bool = False,
        ssd_path: str = EVAL_NVME_PATH,
        ) -> None:
    """
    Run native QEMU with virtio-blk-pci.
    """
    base_cmd: str = build_benchmark_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image,
            rebuild_ovmf=rebuild_ovmf,
            )
    qemu_cmd = add_ovmf_to_qemu_cmd(base_cmd)
    qemu_cmd = add_virtio_blk_nvme_to_qemu_cmd(qemu_cmd, ssd_path)

    if vm_type == "sev":
        qemu_cmd = add_sev_to_qemu_cmd(qemu_cmd)

    print_and_sudo(c, qemu_cmd, pty=True)


# shared code for sev and native qemu virtio blk nvme benchmarks
def exec_benchmark(
        c: Any,
        base_cmd: str,
        dm_benchmark: bool,
        stop_qemu_before_benchmark: bool,
        fio_benchmark: str,
        ignore_warning: bool,
        num_cpus: int,
        await_results: bool,
        benchmark_tag: str,
        ssd_path: str,
        pin: bool,
        qmp_socket_path: str,
        iothreads: bool,
        aio: str,
        noexec: bool,
        fio_job_path: str,
        direct: bool,
        no_flush: bool,
        scsi: bool,
        storage_engine: str = ENGINE_VIRTIO_BLK,
        ) -> None:
    if storage_engine == ENGINE_VIRTIO_BLK:
        qemu_cmd: str = add_virtio_blk_nvme_to_qemu_cmd(
                base_cmd=base_cmd,
                nvme_path=ssd_path,
                ignore_warning=ignore_warning,
                iothreads=iothreads,
                aio=aio,
                direct=direct,
                no_flush=no_flush,
                scsi=scsi,
                )
    elif storage_engine == ENGINE_NVME:
        qemu_cmd: str = add_nvme_to_qemu_cmd(
                base_cmd=base_cmd,
                nvme_path=ssd_path,
                ignore_warning=ignore_warning,
                )
    else:
        err_print(f"Unknown storage engine {storage_engine}")
        exit(1)

    # pin cpus to cmd
    # qemu_cmd: str = f"taskset -c 4-{4+num_cpus-1} {qemu_cmd}"
    # gives one cpu extra- however, we need an extra cpu for qemu IMO
    if pin:
        # pin qemu threads to 8+num_cpus+1(io_thread)
        # (vcpu will be pineed 8-(8+num_cpus-1)
        qemu_cmd: str = f"taskset -c {8+num_cpus+1} {qemu_cmd}"
    else:
        qemu_cmd: str = f"taskset -c 8-{8+num_cpus} {qemu_cmd}"

    if stop_qemu_before_benchmark:
        warn_print("Stopping QEMU")
        stop_qemu(c)

    print_and_sudo(c, qemu_cmd, disown=True)
    timeout = 10
    # wait until qemu is ready
    info_print("Waiting for QEMU to start")
    while ssh_vm(c, cmd="exit").failed:
        info_print(f"QEMU not ready yet. {timeout} tries left")
        time.sleep(1)
        if timeout == 0:
            err_print("VM did not start. Try rebuilding OVMF, Kernel, or Image.")
            exit(1)
        timeout -= 1

    if pin:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        print_and_sudo(c, f"python3 {script_dir}/pin.py {qmp_socket_path}")


    if dm_benchmark:
        fio_filename: str = CRYPTSETUP_TARGET_PATH
        if scsi:
            vm_ssd_path = VM_BENCHMARK_SCSI_PATH
        else:
            vm_ssd_path = VM_BENCHMARK_SSD_PATH
        cryptsetup_open_ssd_in_vm(c, ssh_port=DEFAULT_SSH_FORWARD_PORT, vm_ssd_path=vm_ssd_path)

    else:
        if storage_engine == ENGINE_VIRTIO_BLK:
            # FIXME: we should use ENGINE_VIRITIO_SCSI here
            if scsi:
                fio_filename: str = VM_BENCHMARK_SCSI_PATH
            else:
                fio_filename: str = VM_BENCHMARK_SSD_PATH
        elif storage_engine == ENGINE_NVME:
            fio_filename: str = NVME_VM_BENCHMARK_SSD_PATH
        else:
            err_print(f"Unknown storage engine {storage_engine}")
            exit(1)

    if noexec:
        return

    exec_fio_in_vm(c, ssh_port=DEFAULT_SSH_FORWARD_PORT,
                   fio_job_path=fio_job_path,
                   fio_filename=fio_filename, fio_benchmark=fio_benchmark)

    if await_results:
        await_vm_fio(c, fio_host_output_tag=benchmark_tag)
        # TODO add tag to fio results


@task(help=benchmark_help)
def benchmark_virtio_blk_qemu(
        c: Any,
        vm_type: str = "native",
        num_mem_gb: int = DEFAULT_NUM_MEM_GB,
        num_cpus: int = DEFAULT_NUM_CPUS,
        rebuild_image: bool = False,
        rebuild_ovmf: bool = False,
        dm_benchmark: bool = False,
        stop_qemu_before_benchmark: bool = False,
        fio_benchmark: str = "all",
        ignore_warning: bool = False,
        await_results: bool = False,
        benchmark_tag: str = "sev_virtio_blk",
        ssd_path: str = EVAL_NVME_PATH,
        pin: bool = True,
        qmp_socket_path: str = DEFAULT_QMP_SOCKET_PATH,
        iothreads: bool = True,
        aio: str = "threads",
        noexec: bool = False,
        fio_job_path: str = FIO_VM_JOB_PATH,
        direct: bool = True,
        no_flush: bool = False,
        scsi: bool = False,
        storage_engine: str = ENGINE_VIRTIO_BLK,
        ) -> None:
    """
    Benchmark QEMU with virtio-blk-pci.
    Polling must be enabled in the nixos configuration.
    """
    base_cmd = build_benchmark_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image,
            rebuild_ovmf=rebuild_ovmf,
            qmp_socket_path=qmp_socket_path
            )

    base_cmd = add_ovmf_to_qemu_cmd(base_cmd)

    if vm_type == "sev":
        base_cmd = add_sev_to_qemu_cmd(base_cmd)

    exec_benchmark(
            c,
            base_cmd=base_cmd,
            dm_benchmark=dm_benchmark,
            stop_qemu_before_benchmark=stop_qemu_before_benchmark,
            fio_benchmark=fio_benchmark,
            ignore_warning=ignore_warning,
            num_cpus=num_cpus,
            await_results=await_results,
            benchmark_tag=benchmark_tag,
            ssd_path=ssd_path,
            pin=pin,
            qmp_socket_path=qmp_socket_path,
            iothreads=iothreads,
            aio=aio,
            noexec=noexec,
            fio_job_path=fio_job_path,
            direct=direct,
            no_flush=no_flush,
            scsi=scsi,
            storage_engine=storage_engine,
            )
