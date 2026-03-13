#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional, List
from pathlib import Path
import shlex

from invoke import task

from config import BUILD_DIR, PROJECT_ROOT, LINUX_DIR, SSH_PORT
from qemu import spawn_qemu, QemuVm


@dataclass
class NodeInfo:
    cpus: str
    mem: int
    dist: [int]


@dataclass
class VMResource:
    cpu: int
    memory: int  # GB
    pin_base: int
    numa_node: [int] = None
    vnuma: Optional[NodeInfo] = None


@dataclass
class VMConfig:
    qemu: Path
    image: Path
    ovmf: Path
    kernel: Optional[Path]
    initrd: Optional[Path]
    cmdline: Optional[str]


VMRESOURCES = {}
# AMD servers
VMRESOURCES["vislor"] = {}
VMRESOURCES["vislor"]["small"] = VMResource(cpu=1, memory=8, numa_node=[0], pin_base=8)
VMRESOURCES["vislor"]["medium"] = VMResource(
    cpu=8, memory=64, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["large"] = VMResource(
    cpu=32, memory=256, numa_node=[0], pin_base=0
)
VMRESOURCES["vislor"]["numa"] = VMResource(
    cpu=64, memory=512, numa_node=[0, 1], pin_base=0
)

VMRESOURCES["vislor"]["boot-mem8"] = VMResource(
    cpu=8, memory=8, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-mem16"] = VMResource(
    cpu=8, memory=16, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-mem32"] = VMResource(
    cpu=8, memory=32, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-mem64"] = VMResource(
    cpu=8, memory=64, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-mem128"] = VMResource(
    cpu=8, memory=128, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-mem256"] = VMResource(
    cpu=8, memory=256, numa_node=[0], pin_base=8
)

VMRESOURCES["vislor"]["boot-cpu1"] = VMResource(
    cpu=1, memory=8, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-cpu8"] = VMResource(
    cpu=8, memory=8, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-cpu16"] = VMResource(
    cpu=16, memory=8, numa_node=[0], pin_base=8
)
VMRESOURCES["vislor"]["boot-cpu28"] = VMResource(
    cpu=28, memory=8, numa_node=[0], pin_base=0
)
VMRESOURCES["vislor"]["boot-cpu32"] = VMResource(
    cpu=32, memory=8, numa_node=[0], pin_base=0
)
VMRESOURCES["vislor"]["boot-cpu56"] = VMResource(
    cpu=56, memory=8, numa_node=[0, 1], pin_base=0
)
VMRESOURCES["vislor"]["boot-cpu64"] = VMResource(
    cpu=64, memory=8, numa_node=[0, 1], pin_base=0
)

VMRESOURCES["irene"] = deepcopy(VMRESOURCES["vislor"])
VMRESOURCES["irene"]["large"] = VMResource(
    cpu=32, memory=256, numa_node=[0], pin_base=8
)
VMRESOURCES["irene"]["xlarge"] = VMResource(
    cpu=64, memory=512, numa_node=[0], pin_base=8
)
del VMRESOURCES["irene"]["numa"]

# Intel servers
VMRESOURCES["ian"] = {}
VMRESOURCES["ian"]["small"] = VMResource(cpu=1, memory=8, numa_node=[0], pin_base=8)
VMRESOURCES["ian"]["medium"] = VMResource(cpu=8, memory=64, numa_node=[0], pin_base=8)
VMRESOURCES["ian"]["large"] = VMResource(cpu=32, memory=128, numa_node=[0], pin_base=0)
VMRESOURCES["ian"]["numa"] = VMResource(
    cpu=64, memory=256, numa_node=[0, 1], pin_base=0
)

# configuration when SNC (Sub Numa Clustering) enabled
# VMRESOURCES["sdp"]["large"] = VMResource(
#    cpu=28, memory=128, numa_node=[1], pin_base=28
# )
# VMRESOURCES["sdp"]["numa"] = VMResource(
#    cpu=56, memory=256, numa_node=[0, 1], pin_base=0
# )
# VMRESOURCES["sdp"]["vnuma"] = VMResource(
#    cpu=56,
#    memory=256,
#    numa_node=[0, 1],
#    pin_base=0,
#    vnuma=[
#        NodeInfo(cpus="0-27", mem=128, dist=[12]),
#        NodeInfo(cpus="28-55", mem=128, dist=[]),
#    ],
# )

VMRESOURCES["ian"]["boot-mem8"] = VMResource(cpu=8, memory=8, numa_node=[0], pin_base=8)
VMRESOURCES["ian"]["boot-mem16"] = VMResource(
    cpu=8, memory=16, numa_node=[0], pin_base=8
)
VMRESOURCES["ian"]["boot-mem32"] = VMResource(
    cpu=8, memory=32, numa_node=[0], pin_base=8
)
VMRESOURCES["ian"]["boot-mem64"] = VMResource(
    cpu=8, memory=64, numa_node=[0], pin_base=8
)
VMRESOURCES["ian"]["boot-mem128"] = VMResource(
    cpu=8, memory=128, numa_node=[0], pin_base=8
)
VMRESOURCES["ian"]["boot-mem256"] = VMResource(
    cpu=8, memory=256, numa_node=[0], pin_base=8
)
# VMRESOURCES["ian"]["boot-mem256"] = VMResource(
#    cpu=8, memory=256, numa_node=[0, 1], pin_base=8
# )

VMRESOURCES["ian"]["boot-cpu1"] = VMResource(cpu=1, memory=8, numa_node=[0], pin_base=8)
VMRESOURCES["ian"]["boot-cpu8"] = VMResource(cpu=8, memory=8, numa_node=[0], pin_base=8)
VMRESOURCES["ian"]["boot-cpu16"] = VMResource(
    cpu=16, memory=8, numa_node=[0], pin_base=0
)
VMRESOURCES["ian"]["boot-cpu32"] = VMResource(
    cpu=32, memory=8, numa_node=[0], pin_base=0
)
VMRESOURCES["ian"]["boot-cpu64"] = VMResource(
    cpu=64, memory=8, numa_node=[0, 1], pin_base=0
)

VMRESOURCES["sdp"] = deepcopy(VMRESOURCES["ian"])
VMRESOURCES["sdp"]["large"] = VMResource(cpu=28, memory=128, numa_node=[0], pin_base=28)
VMRESOURCES["sdp"]["xlarge"] = VMResource(cpu=56, memory=256, numa_node=[0], pin_base=0)
VMRESOURCES["sdp"]["numa"] = VMResource(
    cpu=112, memory=512, numa_node=[0, 1], pin_base=0
)
VMRESOURCES["sdp"]["boot-cpu28"] = VMResource(
    cpu=28, memory=8, numa_node=[0], pin_base=0
)
VMRESOURCES["sdp"]["boot-cpu56"] = VMResource(
    cpu=56, memory=8, numa_node=[0, 1], pin_base=0
)


def get_vm_resource(hostname: str, name: str) -> VMResource:
    return VMRESOURCES[hostname][name]


def get_vm_config(name: str, config: dict) -> VMConfig:
    if name == "amd":
        # use kernel same for the "snp"
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/snp-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "amd-normal":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/normal-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "amd-direct":
        return VMConfig(
            qemu=BUILD_DIR / "qemu-amd-sev-snp/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/guest-fs.qcow2",
            ovmf=BUILD_DIR / "ovmf-amd-sev-snp-fd/FV/OVMF.fd",
            kernel=LINUX_DIR / "arch/x86/boot/bzImage",
            initrd=None,
            cmdline=f"root={config['root_dev']} console=hvc0",
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
            cmdline=f"root={config['root_dev']} console=hvc0",
        )
    if name == "intel":
        # use kernel same for the "tdx"
        return VMConfig(
            # qemu="/usr/bin/qemu-system-x86_64",
            # ovmf="/usr/share/ovmf/OVMF.fd",
            qemu=BUILD_DIR / "qemu-tdx/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/tdx-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-tdx-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "intel-normal":
        return VMConfig(
            qemu="/usr/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/normal-guest-image.qcow2",
            ovmf="/usr/share/ovmf/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "intel-direct":
        return VMConfig(
            # qemu="/usr/bin/qemu-system-x86_64",
            qemu=BUILD_DIR / "qemu-tdx/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/guest-fs.qcow2",
            # ovmf="/usr/share/ovmf/OVMF.fd",
            ovmf=BUILD_DIR / "ovmf-tdx-fd/FV/OVMF.fd",
            kernel=LINUX_DIR / "arch/x86/boot/bzImage",
            initrd=None,
            cmdline=f"root={config['root_dev']} console=hvc0",
        )
    if name == "intel-ubuntu":
        return VMConfig(
            qemu="/usr/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/tdx-guest-ubuntu-24.04-generic.qcow2",
            ovmf="/usr/share/ovmf/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "tdx":
        return VMConfig(
            # qemu="/usr/bin/qemu-system-x86_64",
            # ovmf="/usr/share/ovmf/OVMF.fd",
            qemu=BUILD_DIR / "qemu-tdx/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/tdx-guest-image.qcow2",
            ovmf=BUILD_DIR / "ovmf-tdx-fd/FV/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    if name == "tdx-direct":
        return VMConfig(
            # qemu="/usr/bin/qemu-system-x86_64",
            qemu=BUILD_DIR / "qemu-tdx/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/guest-fs.qcow2",
            # ovmf="/usr/share/ovmf/OVMF.fd",
            ovmf=BUILD_DIR / "ovmf-tdx-fd/FV/OVMF.fd",
            kernel=LINUX_DIR / "arch/x86/boot/bzImage",
            initrd=None,
            cmdline=f"root={config['root_dev']} console=hvc0",
        )
    if name == "tdx-ubuntu":
        return VMConfig(
            qemu="/usr/bin/qemu-system-x86_64",
            image=BUILD_DIR / "image/tdx-guest-ubuntu-24.04-generic.qcow2",
            ovmf="/usr/share/ovmf/OVMF.fd",
            kernel=None,
            initrd=None,
            cmdline=None,
        )
    raise ValueError(f"Unknown VM image: {name}")


def get_amd_vm_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("amd", config)
    ssh_port = config["ssh_port"]

    qemu_cmd = f"""
    {vmconfig.qemu}
    -enable-kvm
    -cpu host
    -smp {resource.cpu}
    -m {resource.memory}G
    -machine q35

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
    -device virtio-blk-pci,drive=q2,bootindex=0
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={vmconfig.ovmf},readonly=on

    -nographic
    """

    return shlex.split(qemu_cmd)


def get_amd_vm_direct_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("amd-direct", config)
    ssh_port = config.get("ssh_port", SSH_PORT)
    extra_cmdline = config.get("extra_cmdline", "")

    qemu_cmd = f"""
    {vmconfig.qemu}
    -cpu host
    -enable-kvm
    -smp {resource.cpu}
    -m {resource.memory}G
    -machine q35

    -kernel {vmconfig.kernel}
    -append "{vmconfig.cmdline} {extra_cmdline}"

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
    -device virtio-blk-pci,drive=q2,
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -drive if=pflash,format=raw,unit=0,file={vmconfig.ovmf},readonly=on

    -nographic
    -serial null
    -device virtio-serial
    -chardev stdio,mux=on,id=char0,signal=off
    -mon chardev=char0,mode=readline
    -device virtconsole,chardev=char0,id=vc0,nr=0
    """

    return shlex.split(qemu_cmd)


def get_snp_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("snp", config)
    ssh_port = config["ssh_port"]
    if config["boot_prealloc"]:
        prealloc = "on"
    else:
        prealloc = "off"

    qemu_cmd = f"""
    {vmconfig.qemu}
    -enable-kvm
    -cpu EPYC-v4,host-phys-bits=true
    -smp {resource.cpu}
    -m {resource.memory}G

    -machine q35,memory-backend=ram1,memory-encryption=sev0,vmport=off
    -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,policy=0x30000
    -object memory-backend-memfd,id=ram1,size={resource.memory}G,share=true,prealloc={prealloc}

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
    -device virtio-blk-pci,drive=q2,bootindex=0
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -bios {vmconfig.ovmf}

    -nographic
    """

    return shlex.split(qemu_cmd)


def get_snp_direct_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("amd-direct", config)
    ssh_port = config.get("ssh_port", SSH_PORT)
    extra_cmdline = config.get("extra_cmdline", "")
    if config["boot_prealloc"]:
        prealloc = "on"
    else:
        prealloc = "off"

    qemu_cmd = f"""
    {vmconfig.qemu}
    -enable-kvm
    -cpu EPYC-v4,host-phys-bits=true,+avx512f,+avx512dq,+avx512cd,+avx512bw,+avx512vl,+avx512ifma,+avx512vbmi,+avx512vbmi2,+avx512vnni,+avx512bitalg
    -smp {resource.cpu}
    -m {resource.memory}G

    -machine q35,memory-backend=ram1,memory-encryption=sev0,vmport=off
    -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,policy=0x30000
    -object memory-backend-memfd,id=ram1,size={resource.memory}G,share=true,prealloc={prealloc}

    -kernel {vmconfig.kernel}
    -append "{vmconfig.cmdline} {extra_cmdline}"

    -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
    -device virtio-blk-pci,drive=q2,
    -device virtio-net-pci,netdev=net0
    -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
    -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    -bios {vmconfig.ovmf}

    -nographic
    -serial null
    -device virtio-serial
    -chardev stdio,mux=on,id=char0,signal=off
    -mon chardev=char0,mode=readline
    -device virtconsole,chardev=char0,id=vc0,nr=0
    """

    return shlex.split(qemu_cmd)


def get_intel_qemu_cmd(type: str, resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config(type, config)
    ssh_port = config["ssh_port"]

    qemu_cmd = f"""
    {vmconfig.qemu}
        -enable-kvm
        -cpu host,pmu=off
        -smp {resource.cpu}
        -m {resource.memory}G
        -machine q35,kernel_irqchip=split,hpet=off

        -bios {vmconfig.ovmf}
        -nographic
        -nodefaults
        -serial stdio

        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
        -device virtio-blk-pci,drive=q2,bootindex=0
        -device virtio-net-pci,netdev=net0
        -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
        -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
    """

    return shlex.split(qemu_cmd)


def get_intel_direct_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("intel-direct", config)
    ssh_port = config["ssh_port"]
    extra_cmdline = config.get("extra_cmdline", "")

    if resource.vnuma is not None:
        # FIXME: the current vnuma config is static
        numa_config = f"""
        -object memory-backend-ram,size=128G,prealloc=yes,host-nodes=0,policy=bind,id=node0
        -numa node,nodeid=0,cpus=0-27,memdev=node0
        -object memory-backend-ram,size=128G,prealloc=yes,host-nodes=1,policy=bind,id=node1
        -numa node,nodeid=1,cpus=28-55,memdev=node1
        -numa dist,src=0,dst=1,val=12
        """
    else:
        numa_config = ""

    qemu_cmd = f"""
    {vmconfig.qemu}
        -enable-kvm
        -cpu host,pmu=off
        -smp {resource.cpu}

        -m {resource.memory}G
        -machine q35,kernel_irqchip=split,hpet=off

        {numa_config}

        -kernel {vmconfig.kernel}
        -append "{vmconfig.cmdline} {extra_cmdline}"

        -bios {vmconfig.ovmf}
        -nographic
        -nodefaults

        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
        -device virtio-blk-pci,drive=q2
        -device virtio-net-pci,netdev=net0
        -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
        -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share
        -serial null
        -device virtio-serial
        -chardev stdio,mux=on,id=char0,signal=off
        -mon chardev=char0,mode=readline
        -device virtconsole,chardev=char0,id=vc0,nr=0
    """

    return shlex.split(qemu_cmd)


def get_tdx_qemu_cmd(type, resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config(type, config)
    ssh_port = config["ssh_port"]
    guest_cid = config["guest_cid"]
    if config["boot_prealloc"]:
        prealloc = "on"
    else:
        prealloc = "off"

    qemu_cmd = f"""
    {vmconfig.qemu}
        -enable-kvm
        -cpu host,pmu=off
        -smp {resource.cpu}
        -m {resource.memory}G
        -machine q35,hpet=off,kernel_irqchip=split,confidential-guest-support=tdx,memory-backend=ram1

        -object tdx-guest,id=tdx
        -object memory-backend-ram,id=ram1,size={resource.memory}G,prealloc={prealloc}
        -bios {vmconfig.ovmf}
        -nographic
        -nodefaults
        -serial stdio

        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
        -device virtio-blk-pci,drive=q2,bootindex=0
        -device virtio-net-pci,netdev=net0
        -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
        -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share

        -device vhost-vsock-pci,guest-cid={guest_cid}
    """

    return shlex.split(qemu_cmd)


def get_tdx_direct_qemu_cmd(resource: VMResource, config: dict) -> List[str]:
    vmconfig: VMConfig = get_vm_config("tdx-direct", config)
    ssh_port = config["ssh_port"]
    guest_cid = config["guest_cid"]
    extra_cmdline = config.get("extra_cmdline", "")
    if config["boot_prealloc"]:
        prealloc = "on"
    else:
        prealloc = "off"

    if resource.vnuma is not None:
        memory = f"""
        -object memory-backend-ram,size={resource.memory//2}G,prealloc={prealloc},host-nodes=0,policy=bind,id=node0
        -numa node,nodeid=0,cpus=0-27,memdev=node0
        -object memory-backend-ram,size={resource.memory//2}G,prealloc={prealloc},host-nodes=1,policy=bind,id=node1
        -numa node,nodeid=1,cpus=28-55,memdev=node1
        -numa dist,src=0,dst=1,val=12
        """
    else:
        memory = f"-object memory-backend-ram,id=node0,size={resource.memory}G,prealloc={prealloc}"

    qemu_cmd = f"""
    {vmconfig.qemu}
        -enable-kvm
        -cpu host,pmu=off
        -smp {resource.cpu}
        -m {resource.memory}G
        -machine q35,hpet=off,kernel_irqchip=split,confidential-guest-support=tdx

        -object tdx-guest,id=tdx
        {memory}

        -kernel {vmconfig.kernel}
        -append "{vmconfig.cmdline} {extra_cmdline}"

        -bios {vmconfig.ovmf}
        -nographic
        -nodefaults

        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={vmconfig.image}
        -device virtio-blk-pci,drive=q2
        -device virtio-net-pci,netdev=net0
        -netdev user,id=net0,hostfwd=tcp::{ssh_port}-:22
        -virtfs local,path={PROJECT_ROOT},security_model=none,mount_tag=share

        -serial null
        -device virtio-serial
        -chardev stdio,mux=on,id=char0,signal=off
        -mon chardev=char0,mode=readline
        -device virtconsole,chardev=char0,id=vc0,nr=0

        -device vhost-vsock-pci,guest-cid={guest_cid}
    """

    return shlex.split(qemu_cmd)


def qemu_option_virtio_blk(
    file: Path,  # file or block device to be used as a backend of virtio-blk
    aio: str = "native",  # either of threads, native (POSIX AIO), io_uring
    direct: bool = True,  # if True, QEMU uses O_DIRECT to open the file
    iothread: bool = True,  # if True, use QEMU iothread
    iommu_option: bool = False,  # if True, enable VIRTIO_F_ACCESS_PLATFORM (VIRTIO_F_IOMMU_PLATFORM) feature bit
    # (this is necessary to force bounce buffers in a normal VM for testing)
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

    if iommu_option:
        iommu = ",iommu_platform=on,disable-modern=off,disable-legacy=on"
    else:
        iommu = ""

    if iothread:
        option = f"""
            -blockdev node-name=q1,driver=raw,file.driver={driver},file.filename={file},file.aio={aio},cache.direct={cache_direct},cache.no-flush=off
            -device virtio-blk-pci,drive=q1,iothread=iothread0{iommu}
            -object iothread,id=iothread0
        """
    else:
        option = f"""
            -blockdev node-name=q1,driver=raw,file.driver={driver},file.filename={file},file.aio={aio},cache.direct={cache_direct},cache.no-flush=off
            -device virtio-blk-pci,drive=q1{iommu}
        """

    return shlex.split(option)


def qemu_option_virtio_nic(
    tap="tap0", mtap="mtap0", vhost=False, mq=False, config={}
) -> List[str]:
    """Qreate a virtio-nic with a tap interface.
    If mq is True, then create multiple queues as many as the number of CPUs.

    See justfile for the bridge configuration.
    """

    resource: VMResource = config["resource"]
    iommu_option = config.get("virtio_iommu", False)
    num_cpus = resource.cpu
    if vhost:
        vhost_option = "on"
    else:
        vhost_option = "off"
    if iommu_option:
        iommu = ",iommu_platform=on,disable-modern=off,disable-legacy=on"
    else:
        iommu = ""

    if mq:
        option = f"""
        -netdev tap,id=en0,ifname={mtap},script=no,downscript=no,vhost={vhost_option},queues={num_cpus}
        -device virtio-net-pci,netdev=en0,mq=on,vectors=18{iommu}
        """
    else:
        option = f"""
        -netdev tap,id=en0,ifname={tap},script=no,downscript=no,vhost={vhost_option}
        -device virtio-net-pci,netdev=en0,mq=off,vectors=18{iommu}
        """
        # option = f"""
        #     -netdev bridge,id=en0,br={bridge}
        #     -device virtio-net-pci,netdev=en0
        # """

    return shlex.split(option)


def start_and_attach(qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    """Start a VM and attach to the console (tmux session) to interact with the VM.
    Note 1: The VM automatically terminates when the tmux session is closed.
    Note 2: Ctrl-C goes to the tmux session, not the VM, killing the entier session with the VM.
    """
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(qemu_cmd, numa_node=resource.numa_node) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.attach()
        vm.shutdown()


def ipython(qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    """Start a VM and then start an ipython shell

    Example usage:
    ```
    # Check QEMU's PID
    In [1]: vm.pid
    Out[1]: 823611

    # Send a command to the VM
    In [2]: vm.ssh_cmd(["echo", "ok"])
    $ ssh -i /scratch/masa/CVM_eval/nix/ssh_key -p 2225 -oBatchMode=yes -oStrictHostKeyChecking=no -oConnectTimeout=5 -oUserKnownHostsFile=/dev/null root@localhost -- echo ok
    Warning: Permanently added '[localhost]:2225' (ED25519) to the list of known hosts.
    Out[2]: CompletedProcess(args=['ssh', '-i', '/scratch/masa/CVM_eval/nix/ssh_key', '-p', '2225', '-oBatchMode=yes', '-oStrictHostKeyChecking=no', '-oConnectTimeout=5', '-oUserKnownHostsFile=/dev/null', 'root@localhost', '--', 'echo ok'], returncode=0, stdout='ok\n')
    ```

    Note that the VM automatically terminates when the ipython session is closed.
    """
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        from IPython import embed

        embed()


def ssh_cmd(qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    """Start a VM and then send cmd via ssh
    Example:

    # we can have multiple ssh commands
    inv vm.start --type intel --ssh-cmd "echo hi" --ssh-cmd "ls /" --action ssh-cmd
    """
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    cmds: [str] = kargs["config"]["ssh_cmd"]
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()

        for cmd in cmds:
            cmd_ = shlex.split(cmd)
            vm.ssh_cmd(cmd_)

        vm.shutdown()


def boottime(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    """Measure the boot time of a VM"""
    import boottime

    type: str = kargs["config"]["type"]
    config: dict = kargs["config"]
    kargs["config"]["vmconfig"] = get_vm_config(f"{type}-direct", config)

    boottime.run_boot_test(name, qemu_cmd, pin, **kargs)


def prepare(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    prepare_phoronix(name, qemu_cmd, pin, **kargs)
    prepare_app(name, qemu_cmd, pin, **kargs)


def prepare_phoronix(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from phoronix import install_bench

        install_bench("pts/memory", vm)
        install_bench("pts/npb", vm)
        vm.shutdown()


def prepare_app(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()

        from application import prepare

        prepare(vm)

        vm.shutdown()


def run_phoronix(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    bench_name = kargs["config"]["phoronix_bench_name"]
    if not bench_name:
        print(
            "Please specify the benchmark name using --phoronix-bench-name (e.g., --phoronix-bench-name memory)"
        )
        return

    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        import phoronix

        phoronix.run_phoronix(name, f"{bench_name}", f"pts/{bench_name}", vm)
        vm.shutdown()


def run_mlc(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        import memory

        memory.run_mlc(name, vm)
        vm.shutdown()


def run_blender(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    repeat: int = kargs["config"].get("repeat", 1)
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from application import run_blender

        run_blender(name, vm, repeat=repeat)
        vm.shutdown()


def run_iperf(
    name: str, qemu_cmd: List[str], pin: bool, udp: bool = False, **kargs: Any
):
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from network import run_iperf

        if kargs["config"]["virtio_nic_vhost"]:
            name += f"-vhost"
        if kargs["config"]["virtio_nic_mq"]:
            name += f"-mq"
        if (
            kargs["config"]["virtio_iommu"]
            and "swiotlb" in kargs["config"]["extra_cmdline"]
        ):
            name += f"-swiotlb"
        run_iperf(name, vm, udp=udp)

        vm.shutdown()


def run_memtier(
    name: str, qemu_cmd: List[str], pin: bool, server: str = "redis", **kargs: Any
):
    tls: bool = kargs["config"].get("tls", False)
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from network import run_memtier

        if kargs["config"]["virtio_nic_vhost"]:
            name += f"-vhost"
        if kargs["config"]["virtio_nic_mq"]:
            name += f"-mq"
        if (
            kargs["config"]["virtio_iommu"]
            and "swiotlb" in kargs["config"]["extra_cmdline"]
        ):
            name += f"-swiotlb"
        run_memtier(name, vm, server=server, tls=tls)
        vm.shutdown()


def run_nginx(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any):
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from network import run_nginx

        if kargs["config"]["virtio_nic_vhost"]:
            name += f"-vhost"
        if kargs["config"]["virtio_nic_mq"]:
            name += f"-mq"
        if (
            kargs["config"]["virtio_iommu"]
            and "swiotlb" in kargs["config"]["extra_cmdline"]
        ):
            name += f"-swiotlb"
        run_nginx(name, vm)
        vm.shutdown()


def run_ping(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any):
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from network import run_ping

        if kargs["config"]["virtio_nic_vhost"]:
            name += f"-vhost"
        if kargs["config"]["virtio_nic_mq"]:
            name += f"-mq"
        if (
            kargs["config"]["virtio_iommu"]
            and "swiotlb" in kargs["config"]["extra_cmdline"]
        ):
            name += f"-swiotlb"
        run_ping(name, vm)
        vm.shutdown()


def run_tensorflow(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    repeat: int = kargs["config"].get("repeat", 1)
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from application import run_tensorflow

        run_tensorflow(name, vm, repeat=repeat)
        vm.shutdown()


def run_pytorch(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    repeat: int = kargs["config"].get("repeat", 1)
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from application import run_pytorch

        run_pytorch(name, vm, repeat=repeat)
        vm.shutdown()


def run_sqlite(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    resource: VMResource = kargs["config"]["resource"]
    virtio_blk: Optional[str] = kargs["config"]["virtio_blk"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    dbpath: str = "/tmp/test.db"
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()

        if virtio_blk:
            import storage

            storage.mount_disk(vm, "/dev/vdb", "/mnt", format="auto")
            dbpath = "/mnt/test.db"

            name += f"-{kargs['config']['virtio_blk_aio']}"
            if not kargs["config"]["virtio_blk_direct"]:
                name += f"-nodirect"
            if not kargs["config"]["virtio_blk_iothread"]:
                name += f"-noiothread"
            if (
                kargs["config"]["virtio_iommu"]
                and "swiotlb" in kargs["config"]["extra_cmdline"]
            ):
                name += f"-swiotlb"

        from application import run_sqlite

        run_sqlite(name, vm, dbpath)
        vm.shutdown()


def run_fio(name: str, qemu_cmd: List[str], pin: bool, **kargs: Any) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        import storage

        name += f"-{kargs['config']['virtio_blk_aio']}"
        if not kargs["config"]["virtio_blk_direct"]:
            name += f"-nodirect"
        if not kargs["config"]["virtio_blk_iothread"]:
            name += f"-noiothread"
        if (
            kargs["config"]["virtio_iommu"]
            and "swiotlb" in kargs["config"]["extra_cmdline"]
        ):
            name += f"-swiotlb"
        fio_job = kargs["config"]["fio_job"]
        storage.run_fio(name, vm, fio_job)
        vm.shutdown()


def run_attestation_sev(
    name: str, qemu_cmd: List[str], pin: bool, **kargs: Any
) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from attestation import run_attestation_sev

        run_attestation_sev(name, vm)
        vm.shutdown()


def run_attestation_tdx(
    name: str, qemu_cmd: List[str], pin: bool, **kargs: Any
) -> None:
    resource: VMResource = kargs["config"]["resource"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        vm.wait_for_ssh()
        from attestation import run_attestation_tdx

        run_attestation_tdx(name, vm)
        vm.shutdown()


def do_action(action: str, **kwargs: Any) -> None:
    if action == "attach":
        start_and_attach(**kwargs)
    elif action == "ipython":
        ipython(**kwargs)
    elif action == "ssh-cmd":
        ssh_cmd(**kwargs)
    elif action == "boottime":
        boottime(**kwargs)
    elif action == "prepare":
        prepare(**kwargs)
    elif action == "prepare-phoronix":
        prepare_phoronix(**kwargs)
    elif action == "prepare-app":
        prepare_app(**kwargs)
    elif action == "run-phoronix":
        run_phoronix(**kwargs)
    elif action == "run-mlc":
        run_mlc(**kwargs)
    elif action == "run-blender":
        run_blender(**kwargs)
    elif action == "run-tensorflow":
        run_tensorflow(**kwargs)
    elif action == "run-pytorch":
        run_pytorch(**kwargs)
    elif action == "run-sqlite":
        run_sqlite(**kwargs)
    elif action == "run-fio":
        run_fio(**kwargs)
    elif action == "run-iperf":
        run_iperf(**kwargs)
    elif action == "run-iperf-udp":
        run_iperf(udp=True, **kwargs)
    elif action == "run-memtier":
        run_memtier(server="redis", **kwargs)
    elif action == "run-memtier-memcached":
        run_memtier(server="memcached", **kwargs)
    elif action == "run-nginx":
        run_nginx(**kwargs)
    elif action == "run-ping":
        run_ping(**kwargs)
    elif action == "run-attestation-sev":
        run_attestation_sev(**kwargs)
    elif action == "run-attestation-tdx":
        run_attestation_tdx(**kwargs)
    else:
        raise ValueError(f"Unknown action: {action}")


# ------------------------------------------------------------


# examples:
# inv vm.start --type snp --size small
# inv vm.start --type normal --no-direct
# inv vm.start --type snp --action run-phoronix
@task
def start(
    ctx: Any,
    type: str = "amd",  # amd, snp, intel, tdx
    size: str = "medium",  # small, medium, large, numa
    hostname: str = None,  # by default use the local hostname
    direct: bool = True,  # if True, do direct boot. otherwise boot from the disk
    action: str = "attach",
    ssh_port: int = SSH_PORT,
    guest_cid: int = 11,  # Guest CID for vsock (only for TDX)
    pin: bool = True,  # if True, pin vCPUs
    pin_base: Optional[int] = None,  # pinning base
    extra_cmdline: str = "",  # extra kernel cmdline (only for direct boot)
    root_dev: str = "/dev/vda",  # root filesystem device name (only for direct boot)
    # ssh_cmd options
    ssh_cmd: [str] = [],
    # boot eval options
    boot_trace: bool = True,
    boot_prealloc: bool = True,
    # phoronix options
    phoronix_bench_name: Optional[str] = None,
    # application bench options
    repeat: int = 1,
    virtio_iommu: bool = False,  # enable VIRTIO_F_ACCESS_PLATFORM (VIRTIO_F_IOMMU_PLATFORM) feature bit
    # virtio-nic options
    virtio_nic: bool = False,
    virtio_nic_vhost: bool = False,
    virtio_nic_mq: bool = False,
    virtio_nic_tap: str = "tap_cvm",
    virtio_nic_mtap: str = "mtap_cvm",
    # virtio-blk options
    virtio_blk: Optional[
        str
    ] = None,  # create a virtio-blk backed by a specified file (or drive)
    virtio_blk_aio: str = "native",
    virtio_blk_direct: bool = True,
    virtio_blk_iothread: bool = True,
    tls: bool = False,
    fio_job: str = "test",
    warn: bool = True,
    name_extra: str = "",
) -> None:
    if hostname is None:
        import socket

        hostname = socket.gethostname()
    config: dict = locals()
    resource: VMResource = get_vm_resource(hostname, size)
    config["resource"] = resource

    if direct and (type == "intel-ubuntu" or type == "tdx-ubuntu"):
        raise NotImplementedError(
            "No support of direct boot of ubuntu (use --no-direct option)"
        )

    qemu_cmd: str
    if type == "amd":
        if direct:
            qemu_cmd = get_amd_vm_direct_qemu_cmd(resource, config)
        else:
            qemu_cmd = get_amd_vm_qemu_cmd(resource, config)
    elif type == "snp":
        if direct:
            qemu_cmd = get_snp_direct_qemu_cmd(resource, config)
        else:
            qemu_cmd = get_snp_qemu_cmd(resource, config)
    elif type == "intel" or type == "intel-ubuntu":
        if direct:
            qemu_cmd = get_intel_direct_qemu_cmd(resource, config)
        else:
            qemu_cmd = get_intel_qemu_cmd(type, resource, config)
    elif type == "tdx" or type == "tdx-ubuntu":
        if direct:
            qemu_cmd = get_tdx_direct_qemu_cmd(resource, config)
        else:
            qemu_cmd = get_tdx_qemu_cmd(type, resource, config)
    else:
        raise ValueError(f"Unknown VM type: {type}")

    if virtio_nic:
        qemu_cmd += qemu_option_virtio_nic(
            tap=virtio_nic_tap,
            mtap=virtio_nic_mtap,
            vhost=virtio_nic_vhost,
            mq=virtio_nic_mq,
            config=config,
        )

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
            virtio_blk,
            virtio_blk_aio,
            virtio_blk_direct,
            virtio_blk_iothread,
            virtio_iommu,
        )

    if config["pin_base"] is None:
        config.pop("pin_base", None)
    name = f"{type}-{'direct' if direct else 'disk'}-{size}" + name_extra
    print(f"Starting VM: {name}")
    do_action(action, qemu_cmd=qemu_cmd, pin=pin, name=name, config=config)
