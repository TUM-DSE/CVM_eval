#!/usr/bin/env python3
import os
from typing import Any

import common
from common import print_and_run, REPO_DIR, KERNEL_SRC_DIR, KERNEL_PATH, print_and_run

from invoke import task

# constants
NUM_CPUS = os.cpu_count()

# helpers
def run_in_kernel_devshell(c: Any, cmd: str) -> None:
    """
    Runs a command in the kernel development shell.
    """
    devshell_cmd = f"nix develop {REPO_DIR}#linux --command bash -c '{cmd}'"
    print_and_run(c, devshell_cmd)

# tasks

@task
def configure_debug_kernel(c: Any) -> None:
    """
    Configure the kernel for debugging.
    Executable by commands which mount kernel directly, i.e., do not
    use an own image.
    Not suitable for SEV execution.

    Enables easy development and debugging of kernel.
    """
    with c.cd(KERNEL_SRC_DIR):
        run_in_kernel_devshell(c, f"make defconfig -j{NUM_CPUS}")
        run_in_kernel_devshell(c, "scripts/config \
              --enable GDB_SCRIPTS \
              --enable CVM_IO \
              --enable DEBUG_INFO \
              --enable BPF \
              --enable BPF_SYSCALL \
              --enable BPF_JIT \
              --enable HAVE_EBPF_JIT \
              --enable BPF_EVENTS \
              --enable FTRACE_SYSCALLS \
              --enable FUNCTION_TRACER \
              --enable HAVE_DYNAMIC_FTRACE \
              --enable DYNAMIC_FTRACE \
              --enable HAVE_KPROBES \
              --enable KPROBES \
              --enable KPROBE_EVENTS \
              --enable ARCH_SUPPORTS_UPROBES \
              --enable UPROBES \
              --enable UPROBE_EVENTS \
              --enable DEBUG_FS \
              --enable DEBUG \
              --enable DEBUG_DRIVER \
              --enable DM_CRYPT \
              --enable CRYPTO_XTS")

@task
def configure_sev_kernel(c: Any) -> None:
    """
    Configure the kernel for SEV execution.
    Required for bechmark build.
    """
    print_and_run(c, f"cp {KERNEL_SRC_DIR}/nixconfig {KERNEL_SRC_DIR}/.config")

@task
def build_kernel(c: Any) -> None:
    """
    Builds the kernel with the current set configuration.
    """
    with c.cd(KERNEL_SRC_DIR):
        run_in_kernel_devshell(c, f"yes '' | make -j{NUM_CPUS}")

@task
def clean_kernel(c: Any) -> None:
    """
    Cleans the kernel build artefacts.
    """
    with c.cd(KERNEL_SRC_DIR):
        run_in_kernel_devshell(c, "make mrproper")
