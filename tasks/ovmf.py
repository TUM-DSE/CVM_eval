#!/usr/bin/env python3
import os
from typing import Any

from common import VM_BUILD_DIR, REPO_DIR, print_and_run
from build import make_build_dirs

from invoke import task

# constants

# we set this path as target
OVMF_RO_DIR = os.path.join(VM_BUILD_DIR, "OVMF-ro")
# nix saves it to here
OVMF_RO_FD_DIR = os.path.join(VM_BUILD_DIR, "OVMF-ro-fd")
OVMF_RW_DIR = os.path.join(VM_BUILD_DIR, "OVMF-rw")
UEFI_BIOS_DIR = os.path.join(OVMF_RO_DIR, "FV")
UEFI_BIOS_RO_FD_DIR = os.path.join(OVMF_RO_FD_DIR, "FV")
UEFI_BIOS_CODE_RO_PATH = os.path.join(UEFI_BIOS_RO_FD_DIR, "OVMF_CODE.fd")
UEFI_BIOS_VARS_RO_PATH = os.path.join(UEFI_BIOS_RO_FD_DIR, "OVMF_VARS.fd")
UEFI_BIOS_FD_RW_PATH = os.path.join(OVMF_RW_DIR, "OVMF.fd")
UEFI_BIOS_CODE_RW_PATH = os.path.join(OVMF_RW_DIR, "OVMF_CODE.fd")
UEFI_BIOS_VARS_RW_PATH = os.path.join(OVMF_RW_DIR, "OVMF_VARS.fd")

# nix recipes
NIX_OVMF_AMD_SEV_SNP = os.path.join(REPO_DIR, "#ovmf-amd-sev-snp")


@task(pre=[make_build_dirs])
def make_ovmf(c: Any):
    """
    Builds OVMF for AMD SEV Qemu benchmark.
    """
    print_and_run(c, f"nix build --out-link {OVMF_RO_DIR} {NIX_OVMF_AMD_SEV_SNP}")
    print_and_run(c, f"install -D -m600 {UEFI_BIOS_VARS_RO_PATH} {UEFI_BIOS_VARS_RW_PATH}")
    print_and_run(c, f"install -D -m600 {UEFI_BIOS_CODE_RO_PATH} {UEFI_BIOS_CODE_RW_PATH}")
