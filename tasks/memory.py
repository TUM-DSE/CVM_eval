#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from typing import Optional
from subprocess import CalledProcessError

from config import PROJECT_ROOT
from qemu import QemuVm


def run_mlc(
    name: str,
    vm: QemuVm,
):
    """Run the mlc benchmark on the VM.
    The results are saved in ./bench-result/memory/mlc/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/memory/mlc/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    cmd = [
        "bash",
        "/share/benchmarks/memory/run_mlc.sh",
    ]

    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error running mlc: {output.stderr}")
    lines = output.stdout.split("\n")
    with open(outputdir_host / f"mlc.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")
