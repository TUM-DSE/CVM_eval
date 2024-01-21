#!/usr/bin/env python3
import os
import time
from typing import Any

from colorama import init, Back, Fore, Style
from invoke.runners import Result, Promise

init(autoreset=True)

# constants
REPO_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
KERNEL_SRC_DIR = os.path.join(REPO_DIR, "src", "linux")
KERNEL_PATH = os.path.join(KERNEL_SRC_DIR, "arch", "x86", "boot", "bzImage")

BUILD_DIR = os.path.join(REPO_DIR, "build")
VM_BUILD_DIR = os.path.join(BUILD_DIR, "vm")

RAMDISK_TEMPFS_PATH = os.path.join(os.sep, "mnt", "tmpfs")
RAMDISK_PATH = os.path.join(RAMDISK_TEMPFS_PATH, "file1GB")

FIO_HOST_VM_OUTPUT_DIR = os.path.join(REPO_DIR, "inv-fio-logs")
os.makedirs(FIO_HOST_VM_OUTPUT_DIR, exist_ok=True)
FIO_POSSIBLE_BENCHMARKS = [
        "alat",
        "bw",
        "iops",
        "all"
        ]


# NOTE: only available if bound to nvme driver (not vfio-pci)
EVAL_NVME_PATH = "/dev/nvme1n1"

# helpers
def cmd_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.MAGENTA + msg)

def info_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.BLUE + f"INFO: {msg}")

def warn_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.LIGHTRED_EX + f"WARNING: {msg}")

def err_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.RED + f"ERROR: {msg}")

def check_fail(r: Any) -> Result:
    # check if r is a Result object
    if not r:
        return r
    if isinstance(r, Promise):
        return r
    if r.failed:
        err_print(f"command failed: {r.command}")
        exit(1)
    return r

def print_and_run(c: Any, cmd: str, no_check:bool = False, **kwargs: Any) -> Result:
    cmd_print(cmd)
    time.sleep(1)
    if no_check:
        return c.run(cmd, **kwargs)
    return check_fail(c.run(cmd, **kwargs))
    
def print_and_sudo(c: Any, cmd: str, no_check:bool = False, **kwargs: Any) -> Result:
    cmd_print(cmd)
    time.sleep(1)
    if no_check:
        return c.sudo(cmd, **kwargs)
    return check_fail(c.sudo(cmd, **kwargs))

def warn_nvm_use(nvme_id: str) -> None:
    warn_print(f"using nvme device {nvme_id}")
    input("Press Enter to continue...")


# private
def _get_nix_rev():
    return os.popen("nix eval --raw .#lib.nixpkgsRev 2>/dev/null").read().strip()

# private func dependent constants
NIX_RESULTS_DIR = os.path.join(REPO_DIR, ".git", "nix-results", f"{_get_nix_rev()}")



def build_fio_cmd(
        fio_benchmark: str,
        fio_filename: str,
        fio_job_path: str,
        fio_output_path: str,
        fio_output_format: str = "json",
        ) -> str:
    fio_cmd: str = f"fio {fio_job_path}"
    fio_cmd += f" --filename={fio_filename}"
    fio_cmd += f" --output={fio_output_path}"
    fio_cmd += f" --output-format={fio_output_format}"

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

    return fio_cmd
