#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from config import PROJECT_ROOT
from qemu import QemuVm


def run_attestation(
    name: str,
    vm: QemuVm,
):
    """
    Run the attestation benchmark on the VM.
    The results are saved in ./bench-result/attestation/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/attestation/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    """
    Run the preparation phase to build the snpguest utility in the CVM.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/justfile",
        "prepare",
    ]
    print(f"Preparing attestation")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error preparing attestation: {output.stderr}")

    """
    Gather the attestation measurements.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/justfile",
        "run",
    ]
    print(f"Running attestation experiments")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error running the attestation experiments: {output.stderr}")

    lines = output.stdout.split("\n")
    with open(outputdir_host / "attestation_results.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")
