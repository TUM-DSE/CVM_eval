#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import json
from pathlib import Path
from typing import Any, Optional
import shutil

from invoke import task

from config import PROJECT_ROOT, BUILD_DIR
from procs import run


@functools.lru_cache(maxsize=None)
def nix_build(what: str, build_dir: Path = BUILD_DIR) -> Any:
    """Run nix build and return the result as json."""
    build_dir.mkdir(parents=True, exist_ok=True)
    outpath = build_dir / what.lstrip(".#")
    cmd = ["nix", "build", "--out-link", str(outpath), "--json", what]
    result = run(cmd, cwd=PROJECT_ROOT)
    return json.loads(result.stdout)


@task
def build_ovmf_snp(c: Any) -> None:
    """Build OVMF with AMD SEV-SNP support.

    Output path is ./build/ovmf-amd-sev-snp-fd
    """
    nix_build(".#ovmf-amd-sev-snp")


@task
def build_ovmf_tdx(c: Any) -> None:
    """Build OVMF with Intel TDX support.

    Output path is ./build/ovmf-tdx-fd
    """
    nix_build(".#ovmf-tdx")


@task
def build_qemu_snp(c: Any) -> None:
    """Build QEMU with AMD SEV-SNP support.

    Output path is ./build/qemu-amd-sev-snp
    """
    nix_build(".#qemu-amd-sev-snp")


@task
def build_qemu_tdx(c: Any) -> None:
    """Build QEMU with Intel TDX support.

    Output path is ./build/qemu-tdx
    """
    nix_build(".#qemu-tdx")


def build_guest_image(
    c: Any, target: str, force: bool = False, dst: Path = Path(f"{BUILD_DIR}/image")
) -> None:
    guest_image_name = f"{target}.qcow2"
    if dst:
        dst.mkdir(parents=True, exist_ok=True)
        dst_file = dst / guest_image_name
        if not force and dst_file.exists():
            print(f"{dst_file} already exists. Skipping build.")
            return
    result = nix_build(f".#{target}")
    if dst:
        qcow2 = Path(result[0]["outputs"]["out"]) / "nixos.qcow2"
        cmd = ["install", "-D", "-m666", str(qcow2), str(dst_file)]
        run(cmd)


@task
def build_snp_guest_image(c: Any, force: bool = False) -> None:
    """Build a guest image with AMD SEV-SNP support.

    Output path is ./build/snp-guest-image

    The build result is a read-only. Copy the image to
    ./build/image/snp-guest-image.qcow2
    """

    build_guest_image(c, "snp-guest-image", force=force)


@task
def build_tdx_guest_image(c: Any, force: bool = False) -> None:
    """Build a guest image with Intel TDX support.

    Output path is ./build/tdx-guest-image

    The build result is a read-only. Copy the image to
    ./build/image/tdx-guest-image.qcow2
    """

    build_guest_image(c, "tdx-guest-image", force=force)


@task
def build_normal_guest_image(c: Any, force: bool = False) -> None:
    """Build a norma guest image.

    Output path is ./build/normal-guest-image

    The build result is a read-only. Copy the image to
    ./build/image/normal-guest-image.qcow2
    """

    build_guest_image(c, "normal-guest-image", force=force)


@task
def build_guest_fs(c: Any, force: bool = False) -> None:
    """Build a guest fs image (w/o kernel).

    Output path is ./build/guest-fs

    The build result is a read-only. Copy the image to
    ./build/image/guest-fs.qcow2
    """

    build_guest_image(c, "guest-fs", force=force)


@task
def build_spdk(c: Any) -> None:
    """Build SPDK

    Output path is ./build/spdk
    """
    nix_build(".#spdk")
