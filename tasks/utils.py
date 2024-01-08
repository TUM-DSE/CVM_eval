#!/usr/bin/env python3
import os
from typing import Any, Dict

from common import print_and_run, REPO_DIR, print_and_sudo

from invoke import task

# constants
DEFAULT_SSH_FORWARD_PORT = 2222

SSH_KEY = os.path.join(REPO_DIR, "nix", "ssh_key")

# VM internal paths
VM_BENCHMARK_SSD_PATH = "/dev/vdb"
CRYPTSETUP_TARGET_PATH = "/dev/mapper/target"

FIO_VM_JOB_PATH = "/mnt/blk-bm.fio"

# helpers
# asynchronous only applies if cmd passed
def ssh_vm(c: Any, ssh_port: int, asynchronous: bool = False, cmd: str = "") -> None:
    ssh_cmd: str = f"ssh -i {SSH_KEY} -o 'StrictHostKeyChecking no' -p {ssh_port} root@localhost"
    # difficulty with multiple commands
    if cmd:
        cmd_log_name: str = cmd.split()[0]
        # see https://stackoverflow.com/a/29172
        if asynchronous:
            ssh_cmd += f" 'nohup {cmd} > /mnt/{cmd_log_name}.log 2> /mnt/{cmd_log_name}.err < /dev/null &'"
        else:
            ssh_cmd += f" '{cmd}'"
    print_and_run(c, ssh_cmd, pty=True)

# tasks
@task(help={"ssh_port": "port to connect ssh to"})
def ssh_vm_pty(c: Any, ssh_port: int = DEFAULT_SSH_FORWARD_PORT) -> None:
    """
    SSH into the SEV VM and open terminal.
    """
    ssh_vm(c, ssh_port)

@task
def cryptsetup_open_ssd_in_vm(c: Any, ssh_port: int = DEFAULT_SSH_FORWARD_PORT, vm_ssd_path: str = "/dev/vdb") -> None:
    """
    SSH into the VM and cryptsetup open the SSD.
    """
    ssh_vm(c, ssh_port=ssh_port, cmd=f"yes '' | cryptsetup open {vm_ssd_path} {CRYPTSETUP_TARGET_PATH} no_read_workqueue no_write_workqueue")

# ssh into VM and exec fio
@task(help={"ssh_port": "port to connect ssh to",
            "fio_job_path": "path to fio job file in VM",
            "fio_filename": "filename to which fio writes to"
            })
def exec_fio_in_vm(c: Any, ssh_port: int = DEFAULT_SSH_FORWARD_PORT, fio_job_path=FIO_VM_JOB_PATH, fio_filename: str = "") -> None:
    """
    SSH into the VM and execute fio.
    """
    fio_cmd: str = f"fio {fio_job_path}"
    if fio_filename:
        fio_cmd += f" --filename={fio_filename}"
    ssh_vm(c, ssh_port=ssh_port, asynchronous=True, cmd=fio_cmd)


# clean up
@task
def stop_qemu(c: Any) -> None:
    """
    Stop the QEMU VM.
    """
    print_and_sudo(c, "pkill .qemu-system-x8", warn=True)
