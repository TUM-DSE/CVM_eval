#!/usr/bin/env python3
import os
from typing import Any

from colorama import init, Back, Fore, Style
from invoke.runners import Result, Promise

init(autoreset=True)

# constants
REPO_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
KERNEL_SRC_DIR = os.path.join(REPO_DIR, "src", "linux")
KERNEL_PATH = os.path.join(KERNEL_SRC_DIR, "arch", "x86", "boot", "bzImage")

# helpers
def cmd_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.MAGENTA + msg)

def info_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.BLUE + msg)

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

def print_and_run(c: Any, cmd: str, **kwargs: Any) -> Result:
    cmd_print(cmd)
    return check_fail(c.run(cmd, **kwargs))
    
def print_and_sudo(c: Any, cmd: str, **kwargs: Any) -> Result:
    cmd_print(cmd)
    return check_fail(c.sudo(cmd, **kwargs))

def warn_nvm_use(nvme_id: str) -> None:
    warn_print(f"using nvme device {nvme_id}")
    input("Press Enter to continue...")


# private
def _get_nix_rev():
    return os.popen("nix eval --raw .#lib.nixpkgsRev 2>/dev/null").read().strip()

# private func dependent constants
NIX_RESULTS_DIR = os.path.join(REPO_DIR, ".git", "nix-results", f"{_get_nix_rev()}")
