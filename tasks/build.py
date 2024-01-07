#!/usr/bin/env python3
from typing import Any

from invoke import task

from common import print_and_run, REPO_DIR, KERNEL_SRC_DIR, KERNEL_PATH, NIX_RESULTS_DIR


@task
def build_nixos_debug_image(c: Any) -> None:
    f"""
    Builds a kernel-less NixOS image.
    Can be configured in {REPO_DIR}/nix/modules/configuration.nix.
    """
    print_and_run(c, f"nix build --out-link {NIX_RESULTS_DIR}/nixos-image/ --builders '' .#nixos-image")
    print_and_run(c, f"install -D -m600 '{NIX_RESULTS_DIR}/nixos-image/nixos.img' {KERNEL_SRC_DIR}/nixos.ext4")
