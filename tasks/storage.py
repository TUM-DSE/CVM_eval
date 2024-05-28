#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from config import PROJECT_ROOT
from qemu import QemuVm


def run_fio(
    name: str,
    vm: QemuVm,
    job: str = "test",
    filename: str = "/dev/vdb",
):
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/fio/{name}/{job}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    output = Path("/share") / outputdir / f"{date}.json"
    fio_job = f"/share/config/fio/{job}.fio"
    cmd = [
        "fio",
        f"--filename={filename}",
        f"--output={output}",
        "--output-format=json",
        fio_job,
    ]
    vm.ssh_cmd(cmd)


def mount_disk(vm: QemuVm, dev: str, mountpoint: str = "/mnt", format=False):
    """Mount a disk on the VM"""
    if format:
        vm.ssh_cmd(["sudo", "mkfs.ext4", dev])
    vm.ssh_cmd(["sudo", "mkdir", "-p", mountpoint])
    vm.ssh_cmd(["sudo", "mount", dev, mountpoint])
