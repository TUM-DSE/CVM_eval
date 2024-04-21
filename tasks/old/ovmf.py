#!/usr/bin/env python3
import os
from typing import Any
from pathlib import Path

from common import VM_BUILD_DIR, REPO_DIR, print_and_run
from build import make_build_dirs

from invoke import task

# constants
OVMF_CODE_NAME = "OVMF_CODE.fd"
OVMF_VARS_NAME = "OVMF_VARS.fd"
OVMF_FD_NAME = "OVMF.fd"

# we set this path as target
OVMF_RO_DIR = Path(VM_BUILD_DIR) / "OVMF-ro"
OVMF_RW_DIR = Path(VM_BUILD_DIR) / "OVMF-rw"

# nix saves it to here
OVMF_RO_FD_DIR = Path(VM_BUILD_DIR) / "OVMF-ro-fd" / "FD"
OVMF_CODE_RO_PATH = OVMF_RO_FD_DIR / OVMF_CODE_NAME
OVMF_VARS_RO_PATH = OVMF_RO_FD_DIR / OVMF_VARS_NAME
OVMF_FD_RO_PATH = OVMF_RO_FD_DIR / OVMF_FD_NAME

# default target directory to copy OVMF files for read/write
OVMF_RW_FD_DIR = Path(VM_BUILD_DIR) / "OVMF-rw" / "FD"
OVMF_CODE_RW_PATH = OVMF_RW_DIR / OVMF_CODE_NAME
OVMF_VARS_RW_PATH = OVMF_RW_DIR / OVMF_VARS_NAME

# nix recipes
NIX_OVMF_AMD_SEV_SNP = Path(REPO_DIR) / "#ovmf-amd-sev-snp"


@task(pre=[make_build_dirs],
      help={"ovmf_target_dir": "target directory for OVMF code and vars. Useful if running VMs in parallel."})
def make_ovmf(
        c: Any,
        ovmf_target_dir: str = OVMF_RW_DIR,
        ) -> None:
    """
    Builds OVMF for AMD SEV Qemu benchmark.
    """
    ovmf_code = Path(ovmf_target_dir) / OVMF_CODE_NAME
    ovmf_vars = Path(ovmf_target_dir) / OVMF_VARS_NAME
    ovmf_fd = Path(ovmf_target_dir) / OVMF_FD_NAME

    print_and_run(c, f"nix build --out-link {OVMF_RO_DIR} {NIX_OVMF_AMD_SEV_SNP}")
    print_and_run(c, f"install -D -m600 {OVMF_VARS_RO_PATH} {ovmf_vars}")
    print_and_run(c, f"install -D -m600 {OVMF_CODE_RO_PATH} {ovmf_code}")
    print_and_run(c, f"install -D -m600 {OVMF_FD_RO_PATH} {ovmf_fd}")
