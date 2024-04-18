#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Optional, List
from pathlib import Path
import shlex

from invoke import task

from config import BUILD_DIR, PROJECT_ROOT, LINUX_DIR, SSH_PORT
from qemu import spawn_qemu, QemuVm


@dataclass
class VMResource:
    name: str
    cpu: int
    memory: int  # GB


@dataclass
class VMConfig:
    qemu: Path
    image: Path
    ovmf: Path
    kernel: Optional[Path]
    initrd: Optional[Path]
    cmdline: Optional[str]


def get_vm_resource(name: str) -> VMResource:
    if name == "small":
        return VMResource(name=name, cpu=1, memory=8)
    if name == "medium":
        return VMResource(name=name, cpu=8, memory=64)
    if name == "large":
        return VMResource(name=name, cpu=32, memory=256)
    if name == "large-numa":
        return VMResource(name=name, cpu=64, memory=512)
    raise ValueError(f"Unknown VM config: {name}")


def get_vm_config(name: str) -> VMConfig:
    if name == "normal":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/normal-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "normal-direct":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/guest-fs.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=LINUX_DIR / "arch/x86/boot/bzImage",
            initrd=None,
            cmdline="root=/dev/vda console=hvc0",
        )
    if name == "snp":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/snp-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "snp-direct":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/guest-fs.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=LINUX_DIR / "arch/x86/boot/bzImage",
            initrd=None,
            cmdline="root=/dev/vda console=hvc0",
        )
    raise ValueError(f"Unknown VM image: {name}")


def get_normal_vm_qemu_cmd(resource_name: str, ssh_port) -> List[str]:
    resource: VMResource = get_vm_resource(resource_name)
    config: VMConfig = get_vm_config("normal")

    qemu_cmd = f"""
    {config.qemu}
    -enable-kvm
    -cpu host
    -smp {resource.cpu}
    -m {resource.memory}G
    -machine q35

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={config.image}
    -device virtio-blk-pci,drive=q2,bootindex=0
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={config.ovmf},readonly=on

    -nographic
    """

    return shlex.split(qemu_cmd)


def get_normal_vm_direct_qemu_cmd(resource_name: str, ssh_port) -> List[str]:
    resource: VMResource = get_vm_resource(resource_name)
    config: VMConfig = get_vm_config("normal-direct")

    qemu_cmd = f"""
    {config.qemu}
    -cpu host
    -enable-kvm
    -smp {resource.cpu}
    -m {resource.memory}G
    -machine q35

    -kernel {config.kernel}
    -append "{config.cmdline}"

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={config.image}
    -device virtio-blk-pci,drive=q2,
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={config.ovmf},readonly=on

    -nographic
    -serial null
    -device virtio-serial
    -chardev stdio,mux=on,id=char0,signal=off
    -mon chardev=char0,mode=readline
    -device virtconsole,chardev=char0,id=vc0,nr=0
    """

    return shlex.split(qemu_cmd)


def get_snp_qemu_cmd(resource_name: str, ssh_port) -> List[str]:
    resource: VMResource = get_vm_resource(resource_name)
    config: VMConfig = get_vm_config("snp")

    qemu_cmd = f"""
    {config.qemu}
    -enable-kvm
    -cpu EPYC-v4,host-phys-bits=true
    -smp {resource.cpu}
    -m {resource.memory}G

    -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
    -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0 \
    -object memory-backend-memfd-private,id=ram1,size={resource.memory}G,share=true \

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={config.image}
    -device virtio-blk-pci,drive=q2,bootindex=0
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={config.ovmf},readonly=on

    -nographic
    """

    return shlex.split(qemu_cmd)


def get_snp_direct_qemu_cmd(resource_name: str, ssh_port) -> List[str]:
    resource: VMResource = get_vm_resource(resource_name)
    config: VMConfig = get_vm_config("normal-direct")

    qemu_cmd = f"""
    {config.qemu}
    -enable-kvm
    -cpu EPYC-v4,host-phys-bits=true
    -smp {resource.cpu}
    -m {resource.memory}G

    -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off
    -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0
    -object memory-backend-memfd-private,id=ram1,size={resource.memory}G,share=true

    -kernel {config.kernel}
    -append "{config.cmdline}"

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={config.image}
    -device virtio-blk-pci,drive=q2,
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={config.ovmf},readonly=on

    -nographic
    -serial null
    -device virtio-serial
    -chardev stdio,mux=on,id=char0,signal=off
    -mon chardev=char0,mode=readline
    -device virtconsole,chardev=char0,id=vc0,nr=0
    """

    return shlex.split(qemu_cmd)


def qemu_option_virtio_blk(
    file: Path,  # file or block device to be used as a backend of virtio-blk
    aio: str = "native",  # either of threads, native (POSIX AIO), io_uring
    direct: bool = True,  # if True, QEMU uses O_DIRECT to open the file
    iothread: bool = True,  # if True, use QEMU iothread
) -> List[str]:
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
    # NOTE:
    # - cache.writeback=on by default
    # - aio=native requires cache.direct=on (open file with O_DIRECT)
    # - by default, we use the same configuration as the "cache=none"
    #
    # - aio=threads vs native: https://bugzilla.redhat.com/show_bug.cgi?id=1545721
    # > With aio=native, IO submissions on the host by Qemu are limited to 1
    # > cpu, where as io=threads is multi-cpu.  io=native provides higher
    # > efficiency (less cpu overhead), but cannot scale to the levels io=threads
    # > does.  However, io=threads can consume more cpu as similar IO levels.  If
    # > there is ample CPU on the host, then io=threads will scale better.

    if file.is_block_device():
        driver = "host_device"
    else:
        driver = "file"

    if direct:
        cache_direct = "on"
    else:
        cache_direct = "off"

    if iothread:
        option = f"""
            -blockdev node-name=q1,driver=raw,file.driver={driver},file.filename={file},file.aio={aio},cache.direct={cache_direct},cache.no-flush=off
            -device virtio-blk-pci,drive=q1,iothread=iothread0
            -object iothread,id=iothread0
        """
    else:
        option = f"""
            -blockdev node-name=q1,driver=raw,file.driver={driver},file.filename={file},file.aio={aio},cache.direct={cache_direct},cache.no-flush=off
            -device virtio-blk-pci,drive=q1
        """

    return shlex.split(option)


def start_and_attach(qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    vm: QemuVM
    with spawn_qemu(qemu_cmd) as vm:
        if pin:
            vm.pin_vcpu()
        vm.attach()


def run_phoronix(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    bench_name = kargs["config"]["phoronix_bench_name"]
    if not bench_name:
        print(
            "Please specify the benchmark name using --phoronix-bench-name (e.g., --phoronix-bench-name memory)"
        )
        return

    vm: QemuVM
    with spawn_qemu(qemu_cmd) as vm:
        if pin:
            vm.pin_vcpu()
        vm.wait_for_ssh()
        import phoronix

        phoronix.run_phoronix(name, f"{bench_name}", f"pts/{bench_name}", vm)


def run_fio(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    vm: QemuVM
    with spawn_qemu(qemu_cmd) as vm:
        if pin:
            vm.pin_vcpu()
        vm.wait_for_ssh()
        import storage

        name += f"-{kargs['config']['virtio_blk_aio']}"
        if not kargs["config"]["virtio_blk_direct"]:
            name += f"-nodirect"
        if not kargs["config"]["virtio_blk_iothread"]:
            name += f"-noiothread"
        fio_job = kargs["config"]["fio_job"]
        storage.run_fio(name, vm, fio_job)


def do_action(action: str, **kwargs: Any) -> None:
    if action == "attach":
        start_and_attach(**kwargs)
    elif action == "run-phoronix":
        run_phoronix(**kwargs)
    elif action == "run-fio":
        run_fio(**kwargs)
    else:
        raise ValueError(f"Unknown action: {action}")


# examples:
# inv vm.start --type snp --size small
# inv vm.start --type normal --no-direct
# inv vm.start --type snp --action run-phoronix
@task
def start(
    ctx: Any,
    type: str = "normal",  # normal, snp
    size: str = "medium",  # small, medium, large, large-numa
    direct: bool = True,  # if True, do direct boot. otherwise boot from the disk
    action: str = "attach",
    ssh_port: int = SSH_PORT,
    pin: bool = True,  # if True, pin vCPUs
    # phoronix options
    phoronix_bench_name: Optional[str] = None,
    # virtio-blk options
    virtio_blk: Optional[
        str
    ] = None,  # create a virtio-blk backed by a specified file (or drive)
    virtio_blk_aio: str = "native",
    virtio_blk_direct: bool = True,
    virtio_blk_iothread: bool = True,
    fio_job: str = "test",
    warn: bool = True,
) -> None:
    config: dict = locals()

    qemu_cmd: str
    if type == "normal":
        if direct:
            qemu_cmd = get_normal_vm_direct_qemu_cmd(size, ssh_port)
        else:
            qemu_cmd = get_normal_vm_qemu_cmd(size, ssh_port)
    elif type == "snp":
        if direct:
            qemu_cmd = get_snp_direct_qemu_cmd(size, ssh_port)
        else:
            qemu_cmd = get_snp_qemu_cmd(size, ssh_port)
    else:
        raise ValueError(f"Unknown VM type: {type}")

    if virtio_blk:
        virtio_blk = Path(virtio_blk)
        print(f"Use virtio-blk: {virtio_blk}")
        if virtio_blk.is_block_device():
            if warn:
                print(
                    f"WARN: use {virtio_blk} as a virtio-blk. This overrides the existing disk image. Ok? [y/N]"
                )
                ok = input()
                if ok != "y":
                    return
        elif not virtio_blk.is_file():
            print(f"{virtio_blk} is not a file nor a block device")
            return
        qemu_cmd += qemu_option_virtio_blk(
            virtio_blk, virtio_blk_aio, virtio_blk_direct, virtio_blk_iothread
        )

    name = f"{type}-{'direct' if direct else 'disk'}-{size}"
    print(f"Starting VM: {name}")
    do_action(action, qemu_cmd=qemu_cmd, pin=pin, name=name, config=config)
