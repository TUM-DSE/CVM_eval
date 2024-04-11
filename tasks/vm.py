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


def start_and_attach(qemu_cmd: List[str], pin) -> None:
    qemu: QemuVM
    with spawn_qemu(qemu_cmd) as qemu:
        if pin:
            qemu.pin_vcpu()
        qemu.attach()


@task
def start_vm_disk(
    ctx: Any, name: str = "medium", ssh_port: int = SSH_PORT, pin: bool = True
) -> None:
    qemu_cmd = get_normal_vm_qemu_cmd(name, ssh_port)
    start_and_attach(qemu_cmd, pin)


@task
def start_vm_direct(
    ctx: Any, name: str = "medium", ssh_port: int = SSH_PORT, pin: bool = True
) -> None:
    qemu_cmd = get_normal_vm_direct_qemu_cmd(name, ssh_port)
    start_and_attach(qemu_cmd, pin)


# XXX: SNP requries sudo
@task
def start_snp_disk(
    ctx: Any, name: str = "medium", ssh_port: int = SSH_PORT, pin: bool = True
) -> None:
    qemu_cmd = get_snp_qemu_cmd(name, ssh_port)
    start_and_attach(qemu_cmd, pin)


@task
def start_snp_direct(
    ctx: Any, name: str = "medium", ssh_port: int = SSH_PORT, pin: bool = True
) -> None:
    qemu_cmd = get_snp_direct_qemu_cmd(name, ssh_port)
    start_and_attach(qemu_cmd, pin)
