#!/usr/bin/env python3
import os
import time
from typing import Any, Dict

from invoke.runners import Result

from common import EVAL_NVME_PATH, err_print, print_and_run, REPO_DIR, print_and_sudo, warn_nvm_use, warn_print

from invoke import task

# constants
DEFAULT_SSH_FORWARD_PORT = 2222

SSH_KEY = os.path.join(REPO_DIR, "nix", "ssh_key")

# VM internal paths
VM_BENCHMARK_SSD_PATH = "/dev/vdb"
CRYPTSETUP_TARGET_NAME = "target"
CRYPTSETUP_TARGET_PATH = f"/dev/mapper/{CRYPTSETUP_TARGET_NAME}"

FIO_VM_JOB_PATH = "/mnt/blk-bm.fio"
FIO_VM_OUTPUT_PATH = "/mnt/blk-bm.log"
FIO_HOST_VM_OUTPUT_DIR = os.path.join(REPO_DIR, "inv-fio-logs")
os.makedirs(FIO_HOST_VM_OUTPUT_DIR, exist_ok=True)
FIO_POSSIBLE_BENCHMARKS = [
        "alat",
        "bw",
        "iops",
        "all"
        ]

# helpers
# asynchronous only applies if cmd passed
def ssh_vm(c: Any, ssh_port: int = DEFAULT_SSH_FORWARD_PORT, asynchronous: bool = False, cmd: str = "", warn: bool = True) -> Result:
    ssh_cmd: str = f"ssh -i {SSH_KEY} -o 'StrictHostKeyChecking no' -p {ssh_port} root@localhost"
    # difficulty with multiple commands
    if cmd:
        ssh_cmd += " -t"
        cmd_log_name: str = cmd.split()[0]
        # see https://stackoverflow.com/a/29172
        if asynchronous:
            # id based on date time
            cmd_log_name += f"-{time.strftime('%Y-%m-%d-%H-%M-%S')}"
            ssh_cmd += f" 'tmux new-session -d -s {cmd_log_name}-session \"{cmd}\"'"
        else:
            ssh_cmd += f" '{cmd}'"
    return print_and_run(c, ssh_cmd, pty=True, warn=warn)

@task
def notify_terminal_after_completion(c: Any) -> None:
    """
    Notify terminal after completion.
    """
    while True:
        print_and_run(c, "tput bel")
        time.sleep(1)

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
    ssh_vm(c, ssh_port=ssh_port, cmd=f"yes \"\" | cryptsetup open {vm_ssd_path} {CRYPTSETUP_TARGET_NAME} no_read_workqueue no_write_workqueue", warn=False)

# ssh into VM and exec fio
@task(help={"ssh_port": "port to connect ssh to",
            "fio_job_path": "path to fio job file in VM",
            "fio_filename": "filename to which fio writes to",
            "fio_output_path": "path to fio output file",
            "fio_benchmark": f"benchmark to run, one of {FIO_POSSIBLE_BENCHMARKS}"
            })
def exec_fio_in_vm(
        c: Any,
        ssh_port: int = DEFAULT_SSH_FORWARD_PORT,
        fio_job_path=FIO_VM_JOB_PATH,
        fio_filename: str = VM_BENCHMARK_SSD_PATH,
        fio_output_path: str = FIO_VM_OUTPUT_PATH,
        fio_benchmark: str = "all"
        ) -> None:
    """
    SSH into the VM and execute fio.
    """
    fio_cmd: str = f"fio {fio_job_path}"
    fio_cmd += f" --filename={fio_filename}"
    fio_cmd += f" --output={fio_output_path}"

    if fio_benchmark not in FIO_POSSIBLE_BENCHMARKS:
        warn_print(f"custom benchmark {fio_benchmark} not in {FIO_POSSIBLE_BENCHMARKS}")
        warn_print("using custom benchmark 'as is' in `--section`")
        

    if fio_benchmark == "all":
        pass
    elif fio_benchmark == "alat":
        for bench_id in ["reandread", "randwrite", "read", "write"]:
            fio_cmd += f" --section=alat\\ {bench_id}"
    elif fio_benchmark == "bw":
        for bench_id in ["read", "write"]:
            fio_cmd += f" --section=bw\\ {bench_id}"
    elif fio_benchmark == "iops":
        for bench_id in ["randread", "randwrite", "rwmixread", "rwmixwrite"]:
            fio_cmd += f" --section=iops\\ {bench_id}"
    else:
        breaked_fio_benchmark = fio_benchmark.replace(' ', '\\ ')
        fio_cmd += f" --section={breaked_fio_benchmark}"

    ssh_vm(c, ssh_port=ssh_port, asynchronous=True, cmd=fio_cmd)

@task
def await_vm_fio(
        c: Any,
        ssh_port: int = DEFAULT_SSH_FORWARD_PORT,
        fio_vm_output_path: str = FIO_VM_OUTPUT_PATH,
        fio_host_output_tag: str = ""
        ) -> None:
    """
    Wait until fio in VM is done.
    Thereafter, copy the fio output file from VM to host.
    """
    # assert fio is running
    if ssh_vm(c, ssh_port=ssh_port, cmd="pgrep fio").failed:
        err_print("fio is not running in VM")
        exit(1)

    while ssh_vm(c, ssh_port=ssh_port, cmd="pgrep fio").ok:
        time.sleep(10)
    
    fio_filename = f"fio-{time.strftime('%Y-%m-%d-%H-%M-%S')}.log"
    if fio_host_output_tag:
        fio_filename = f"{fio_host_output_tag}-{fio_filename}"
    # write current date time into string
    fio_host_output_path = os.path.join(FIO_HOST_VM_OUTPUT_DIR, fio_filename)


    # copy fio output file from VM to host
    if print_and_run(c, f"scp -i {SSH_KEY} -o 'StrictHostKeyChecking no' -P {ssh_port} root@localhost:{fio_vm_output_path} {fio_host_output_path}", pty=True, warn=True).failed:
        err_print("scp failed to copy fio output file from VM to host")
        exit(1)


# clean up
@task
def stop_qemu(c: Any) -> None:
    """
    Stop the QEMU VM.
    """
    print_and_sudo(c, "pkill .qemu-system-x8", warn=True)

# cryptsetup utils
@task(help={"ssd_path": "Path to SSD"})
def cryptsetup_crypt_only(
        c: Any,
        ssd_path: str = EVAL_NVME_PATH,
        ) -> None:
    """
    Cryptsetup crypt only.
    """
    warn_nvm_use(ssd_path)
    print_and_sudo(c, f"cryptsetup -v -q luksFormat --type luks2 {ssd_path}", warn=True)

@task(help={"ssd_path": "Path to SSD"})
def cryptsetup_crypt_integrity(
        c: Any,
        ssd_path: str = EVAL_NVME_PATH,
        ) -> None:
    """
    Cryptsetup crypt with integrity.
    """
    warn_nvm_use(ssd_path)
    print_and_sudo(c, f"yes '' | cryptsetup -v -q luksFormat --type luks2 --integrity hmac-sha256 {ssd_path}")
