#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import json
from pathlib import Path
from typing import Any

from invoke import task

from config import PROJECT_ROOT, BUILD_DIR
from procs import run


@functools.lru_cache(maxsize=None)
def nix_build(what: str, build_dir: Path = BUILD_DIR) -> Any:
    build_dir.mkdir(parents=True, exist_ok=True)
    outpath = build_dir / what.lstrip(".#")
    cmd = ["nix", "build", "--out-link", str(outpath), "--json", what]
    result = run(cmd, cwd=PROJECT_ROOT)
    return json.loads(result.stdout)


@task
def build_omvf_snp(c: Any) -> None:
    """Build OVMF with AMD SEV-SNP support.

    Output path is ./build/ovmf-amd-sev-snp-fd
    """
    nix_build(".#ovmf-amd-sev-snp")


@task
def build_qemu_snp(c: Any) -> None:
    """Build QEMU with AMD SEV-SNP support.

    Output path is ./build/qemu-amd-sev-snp
    """
    nix_build(".#qemu-amd-sev-snp")
