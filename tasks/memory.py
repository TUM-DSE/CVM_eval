#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from subprocess import CalledProcessError

from invoke import task
import numpy as np

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


@task
def show_mmap_result(cx: Any, cvm: str = "snp", size: str = "medium"):
    """Parse mmap measure log and show the result"""
    if cvm == "snp":
        vm = "amd"
    else:
        vm = "intel"

    RESULT_DIR = PROJECT_ROOT / f"bench-result/memory/mmap-time"

    for v in [vm, cvm]:
        for n in ["1st", "2nd"]:
            log = RESULT_DIR / f"{v}-direct-{size}/{n}.txt"
            result = []
            with open(log, "r") as f:
                lines = f.readlines()
                result = [float(line) for line in lines]
            print(
                f"{v},{n},{np.median(result):.3f},{np.mean(result):.3f},{np.std(result):.3f}"
            )

    if cvm == "tdx":
        for n in ["1st", "2nd"]:
            log = RESULT_DIR / f"tdx-direct-{size}-no-prealloc/{n}.txt"
            result = []
            with open(log, "r") as f:
                lines = f.readlines()
                result = [float(line) for line in lines]
            print(
                f"tdx-no-prealloc,{n},{np.median(result):.3f},{np.mean(result):.3f},{np.std(result):.3f}"
            )
