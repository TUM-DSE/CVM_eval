#!/usr/bin/env python3
# contains common build tasks
import os
from typing import Any

from invoke import task

from common import print_and_run, REPO_DIR, KERNEL_SRC_DIR, KERNEL_PATH, NIX_RESULTS_DIR, VM_BUILD_DIR, BUILD_DIR
# warning: dependency
from kernel import build_kernel, configure_debug_kernel, configure_sev_kernel, build_kernel
from tasks.utils import notify_terminal_after_completion


# constants
# NOTE: if we want to run VMs in parallel, we need separate
QCOW2_NAME = "nixos.qcow2"
IMG_RO_DIR = os.path.join(VM_BUILD_DIR, "img-ro")
IMG_RO_PATH = os.path.join(IMG_RO_DIR, QCOW2_NAME)
IMG_RW_DIR = os.path.join(VM_BUILD_DIR, "img-rw")
IMG_RW_PATH = os.path.join(IMG_RW_DIR, QCOW2_NAME)

NIX_DEBUG_IMG_RECIPE = os.path.join(REPO_DIR, "#nixos-image")
NIX_BENCHMARK_IMG_RECIPE = os.path.join(REPO_DIR, "#guest-image")

@task
def make_build_dirs(c: Any):
    """
    Creates build directories.
    """
    os.makedirs(VM_BUILD_DIR, exist_ok=True)


@task(pre=[configure_debug_kernel])
def build_nixos_debug_image(c: Any) -> None:
    """
    Builds a kernel-less NixOS image.
    Can be configured in {REPO_DIR}/nix/modules/configuration.nix.
    """
    print_and_run(c, f"nix build --out-link {NIX_RESULTS_DIR}/nixos-image/ --builders '' {NIX_DEBUG_IMG_RECIPE}")
    print_and_run(c, f"install -D -m600 '{NIX_RESULTS_DIR}/nixos-image/nixos.img' {KERNEL_SRC_DIR}/nixos.ext4")


@task(pre=[make_build_dirs],
      help={"cvm_io": "enable CVM_IO",
            "notify": "notify terminal after completion",
            "kernel_only": "build kernel only"})
def build_nixos_bechmark_image(
        c: Any,
        cvm_io: bool = False,
        notify: bool = False,
        kernel_only: bool = False,
        ) -> None:
    """
    Builds NixOS image w/ custom kernel
    Configurable in {REPO_DIR}/nix/native-guest-config.nix.
    """
    # configure sev kernel ( not as pretask as we pass param )
    # configure_sev_kernel, build_kernel
    configure_sev_kernel(c, cvm_io=cvm_io)
    build_kernel(c)
    if kernel_only:
        return
    # update kernel src to allow cached builds (vs building from scratch)
    print_and_run(c, "nix flake lock --update-input kernelSrc")
    print_and_run(c, f"nix build --out-link {IMG_RO_DIR} --builders '' {NIX_BENCHMARK_IMG_RECIPE}")
    print_and_run(c, f"install -D -m600 {IMG_RO_PATH} {IMG_RW_PATH}")
    if notify:
        notify_terminal_after_completion()

@task
def make_clean(c: Any) -> None:
    """
    Cleans build artefacts.
    """
    print_and_run(c, f"rm -rf {BUILD_DIR}")
