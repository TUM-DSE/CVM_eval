#!/usr/bin/env python3
import os
import time
from typing import Any

import kernel
import utils

from spdk import VHOST_CONTROLLER_NAME

from common import info_print, warn_nvm_use, print_and_run, print_and_sudo, err_print, REPO_DIR, VM_BUILD_DIR, warn_print

from invoke import task
# warning: dependency
from ovmf import UEFI_BIOS_CODE_RW_PATH, UEFI_BIOS_VARS_RW_PATH, make_ovmf
from build import IMG_RW_PATH, build_nixos_bechmark_image
from utils import exec_fio_in_vm, ssh_vm, DEFAULT_SSH_FORWARD_PORT, cryptsetup_open_ssd_in_vm, VM_BENCHMARK_SSD_PATH, CRYPTSETUP_TARGET_PATH, stop_qemu

# constants
QEMU_BIN = "qemu-system-x86_64"

## paths
# NOTE: only available if bound to nvme driver (not vfio-pci)
EVAL_NVME_PATH = "/dev/nvme1n1"


# build artefacts
## OVMF

# invariant to any qemu execution
def build_base_qemu_cmd(
        c: Any,
        ssh_forward_port: int,
        num_mem_gb:int = 16,
        num_cpus: int = 4
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
        "-device virtconsole,chardev=char0,id=cvmio,nr=0"



# vm_img_path,
#         "-blockdev qcow2,node-name=q2,file.driver=file,file.filename={vm_img_path}" \
#         "-device virtio-blk-pci,drive=q2" \

def build_debug_qemu_cmd(
        c: Any,
        kernel_path: str = kernel.KERNEL_PATH,
        extra_kernel_cmdline: str = "",
        num_mem_gb: int = 16,
        num_cpus: int = 4
        ) -> str:
    base_cmd = build_base_qemu_cmd(
            c,
            DEFAULT_SSH_FORWARD_PORT,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus
            )
    # NOTE: root may have to be changed if extra disk is mounted (to /dev/vdb)
    return f"{base_cmd} " \
        f"-kernel '{kernel_path}' " \
        f"-drive format=raw,file={kernel.KERNEL_SRC_DIR}/nixos.ext4,id=mydrive,if=virtio " \
        f"-append 'console=hvc0 root=/dev/vdb nokaslr loglevel=7 {extra_kernel_cmdline}' " \
        f"-virtfs local,path={REPO_DIR},security_model=none,mount_tag=home"

def build_benchmark_qemu_cmd(
        c: Any,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        rebuild_image: bool = False
        ):
    base_cmd = build_base_qemu_cmd(
            c,
            DEFAULT_SSH_FORWARD_PORT,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus
            )
    if rebuild_image or not os.path.exists(IMG_RW_PATH):
        build_nixos_bechmark_image(c)
    # no need to rebuild ovmf if already exist
    if not (os.path.exists(UEFI_BIOS_CODE_RW_PATH) and os.path.exists(UEFI_BIOS_VARS_RW_PATH)):
        make_ovmf(c)

    return f"{base_cmd} " \
        f"-blockdev qcow2,node-name=q2,file.driver=file,file.filename={IMG_RW_PATH} " \
        "-device virtio-blk-pci,drive=q2 " \
        f"-drive if=pflash,format=raw,unit=0,file={UEFI_BIOS_CODE_RW_PATH},readonly=on " \
        f"-drive if=pflash,format=raw,unit=1,file={UEFI_BIOS_VARS_RW_PATH}"

def build_sev_qemu_cmd(
        c: Any,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        rebuild_image: bool = False
        ):
    base_cmd = build_benchmark_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image
            )

    return f"{base_cmd} " \
        "-machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off " \
        "-object memory-backend-memfd-private,id=ram1,size=16G,share=true " \
        "-object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA"

def build_sev_virtio_blk_qemu_cmd(
        c: Any,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        rebuild_image: bool = False,
        nvme_path: str = EVAL_NVME_PATH
        ):
    base_cmd = build_sev_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image
            )
    return f"{base_cmd} " \
        f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path} " \
        "-device virtio-blk,drive=q1"

def build_debug_poll_qemu_cmd(
        c: Any,
        ignore_warning: bool = False,
        num_queues: int = 4,
        num_poll_queues: int = 2,
        nvme_path: str = EVAL_NVME_PATH
        ) -> str:

    if not ignore_warning:
        warn_nvm_use(nvme_path)

    base_cmd = build_debug_qemu_cmd(c, extra_kernel_cmdline=f"virtio_blk.poll_queues={num_poll_queues}")
    return f"{base_cmd} " \
        "-object iothread,id=iothread0 " \
        f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},cache.direct=on " \
        f"-device virtio-blk,drive=q1,iothread=iothread0,num-queues={num_queues}"

def build_debug_vhost_blk_poll_qemu_cmd(
        c: Any,
        num_queues: int = 4,
        num_poll_queues: int = 2,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        ) -> str:
    base_cmd = build_debug_qemu_cmd(
            c,
            extra_kernel_cmdline=f"virtio_blk.poll_queues={num_poll_queues}",
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus
            )
    return f"{base_cmd} " \
        f"-object memory-backend-file,id=mem,size={num_mem_gb}G,mem-path=/dev/hugepages,share=on " \
        "-numa node,memdev=mem " \
        f"-chardev socket,id=char1,path=/var/tmp/{VHOST_CONTROLLER_NAME} " \
        f"-device vhost-user-blk-pci,id=blk0,chardev=char1,num-queues={num_queues}"



# tasks

@task(help={
    'ignore_warning': "Ignore warning about using NVMe device",
    'num_queues': "Number of virtio-blk queues",
    'num_poll_queues': "Number of virtio-blk poll queues",
    })
def run_debug_virtio_blk_poll_qemu(
        c: Any,
        ignore_warning: bool = False,
        num_queues: int = 4,
        num_poll_queues: int = 2
        ) -> None:
    """
    Run native debug QEMU with virtio-blk-pci and poll mode enabled.
    Uses kernel from {kernel.KERNEL_PATH}.
    """
    qemu_cmd: str = build_debug_poll_qemu_cmd(
            c,
            ignore_warning,
            num_queues,
            num_poll_queues
            )
    print_and_sudo(c, qemu_cmd, pty=True)


@task(help={
    'num_queues': "Number of virtio-blk queues",
    'num_poll_queues': "Number of virtio-blk poll queues",
    'num_mem_gb': "Number of GBs of memory",
    'num_cpus': "Number of CPUs",
    })
def run_debug_vhost_blk_poll_qemu(
        c: Any,
        num_queues: int = 4,
        num_poll_queues: int = 2,
        num_mem_gb: int = 16,
        num_cpus: int = 4
        ) -> None:
    """
    Run native debug QEMU with vhost-blk-pci and poll mode enabled.
    """
    if not os.path.exists(os.path.join(os.sep, "var", "tmp", VHOST_CONTROLLER_NAME)):
        err_print(f"vhost target not running. run setup_vhost_target first")
        exit(1)
    qemu_cmd: str = build_debug_vhost_blk_poll_qemu_cmd(
            c,
            num_queues,
            num_poll_queues,
            num_mem_gb,
            num_cpus
            )
    print_and_sudo(c, qemu_cmd, pty=True)

@task(help={
    'num_mem_gb': "Number of GBs of memory",
    'num_cpus': "Number of CPUs",
    'rebuild_image': "Rebuild nixos image (also recompiles kernel- takes a while)",
    })
def run_sev_virtio_blk_qemu(
        c: Any,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        rebuild_image: bool = False,
        ) -> None:
    """
    Run Qemu SEV guest with virtio-blk-pci to NVMe SSD.
    """
    qemu_cmd: str = build_sev_virtio_blk_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image
            )
    print_and_sudo(c, qemu_cmd, pty=True)


@task(help={
    'num_mem_gb': "Number of GBs of memory",
    'num_cpus': "Number of CPUs",
    'rebuild_image': "Rebuild nixos image (also recompiles kernel- takes a while)",
    'dm_benchmark': "Runs fio on dm devices on top of SSD"
    })
def benchmark_sev_virtio_blk_qemu(
        c: Any,
        num_mem_gb: int = 16,
        num_cpus: int = 4,
        rebuild_image: bool = False,
        dm_benchmark: bool = False,
        stop_qemu_before_benchmark: bool = False,
        ) -> None:
    """
    Benchmark SEV QEMU with virtio-blk-pci.
    Polling must be enabled in the nixos configuration.
    """
    if stop_qemu_before_benchmark:
        warn_print("Stopping QEMU")
        stop_qemu(c)

    qemu_cmd: str = build_sev_virtio_blk_qemu_cmd(
            c,
            num_mem_gb=num_mem_gb,
            num_cpus=num_cpus,
            rebuild_image=rebuild_image
            )
    print_and_sudo(c, qemu_cmd, disown=True)
    timeout = 10
    # wait until qemu is ready
    info_print("Waiting for QEMU to start")
    while print_and_run(c, no_check=True, cmd=f"nc -z localhost {DEFAULT_SSH_FORWARD_PORT}", warn=True).failed:
        info_print(f"QEMU not ready yet. {timeout} seconds left")
        time.sleep(1)
        if timeout == 0:
            err_print("QEMU did not start")
            exit(1)
        timeout -= 1
    if dm_benchmark:
        fio_filename: str = CRYPTSETUP_TARGET_PATH
        cryptsetup_open_ssd_in_vm(c, ssh_port=DEFAULT_SSH_FORWARD_PORT, vm_ssd_path=VM_BENCHMARK_SSD_PATH)
    else:
        fio_filename: str = VM_BENCHMARK_SSD_PATH

    exec_fio_in_vm(c, ssh_port=DEFAULT_SSH_FORWARD_PORT, fio_filename=fio_filename)


