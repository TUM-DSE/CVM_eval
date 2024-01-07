#!/usr/bin/env python3
import os
from typing import Any

import kernel
import utils
from common import warn_nvm_use

from invoke import task

# constants
QEMU_BIN = "qemu-system-x86_64"

## default paths
REPO_DIR = os.path.dirname(os.path.realpath(__file__))
EVAL_NVME_PATH = "/dev/nvme1n1"


# invariant to any qemu execution
def build_base_qemu_cmd(
        c: Any,
        ssh_forward_port: int,
        num_cpus: int = 4,
        num_mem_gb:int = 16,
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
        ) -> str:
    base_cmd = build_base_qemu_cmd(c, utils.DEFAULT_NATIVE_SSH_FORWARD_PORT)
    # NOTE: root may have to be changed if extra disk is mounted (to /dev/vdb)
    return f"{base_cmd} " \
        f"-kernel '{kernel_path}' " \
        f"-drive format=raw,file={kernel.KERNEL_SRC_DIR}/nixos.ext4,id=mydrive,if=virtio " \
        f"-append 'console=hvc0 root=/dev/vdb nokaslr loglevel=7 {extra_kernel_cmdline}' " \
        f"-virtfs local,path={REPO_DIR},security_model=none,mount_tag=home"
        

def build_debug_poll_qemu_cmd(
        c: Any,
        ignore_warning: bool = False,
        num_queues: int = 4,
        num_poll_queues: int = 2,
        nvme_path: str = EVAL_NVME_PATH
        ) -> str:

    if not ignore_warning:
        warn_nvm_use(nvme_path)

    base_cmd = build_debug_qemu_cmd(c, extra_kernel_cmdline=f"virtio_blk.num_poll_queues={num_poll_queues}")
    return f"{base_cmd} " \
        "-object iothread,id=iothread0 " \
        f"-blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={nvme_path},cache.direct=on " \
        f"-device virtio-blk,drive=q1,iothread=iothread0,num-queues={num_queues}"


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
    qemu_cmd = build_debug_poll_qemu_cmd(
            c,
            ignore_warning,
            num_queues,
            num_poll_queues
            )
    print(qemu_cmd)
    c.sudo(qemu_cmd, pty=True)
