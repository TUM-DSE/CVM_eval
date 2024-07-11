#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from config import PROJECT_ROOT
from qemu import QemuVm

import subprocess


def run_attestation_sev(
    name: str,
    vm: QemuVm,
):
    """
    Run the attestation benchmark on the SEV VM.
    The results are saved in ./bench-result/attestation/sev/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/attestation/sev/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    """
    Run the preparation phase to build the snpguest utility in the CVM.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/sev/justfile",
        "prepare",
    ]
    print(f"Preparing SEV attestation")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error preparing attestation: {output.stderr}")

    """
    Gather the attestation measurements.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/sev/justfile",
        "run",
    ]
    print(f"Running SEV attestation experiments")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error running the attestation experiments: {output.stderr}")

    lines = output.stdout.split("\n")
    with open(outputdir_host / "attestation_results.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_attestation_tdx(
    name: str,
    vm: QemuVm,
):
    """
    Run the attestation benchmark on the TDX VM.
    The results are saved in ./bench-result/attestation/tdx/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/attestation/tdx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    """
    Mount the shared directory in the TDX ubuntu-based guest
    """
    cmd = [
        "mkdir",
        "-p",
        "/share",
    ]
    print(f"Creating /share directory in the TDX guest")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error creating /share directory in the TDX guest: {output.stderr}")

    cmd = [
        "mount",
        "-t",
        "9p",
        "-o",
        "trans=virtio,version=9p2000.L",
        "share",
        "/share",
    ]
    print(f"Mounting /share directory in the TDX guest")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error Mounting /share directory in the TDX guest: {output.stderr}")

    """
    Run the preparation phase to build the snpguest utility in the CVM.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/tdx/justfile",
        "prepare",
    ]
    print(f"Preparing TDX attestation")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error preparing attestation: {output.stderr}")

    """
    Gather the attestation measurements.
    """
    cmd = [
        "just",
        "-f",
        "/share/benchmarks/attestation/tdx/justfile",
        "run",
    ]
    print(f"Running TDX attestation experiments")
    output = vm.ssh_cmd(cmd)
    if output.returncode != 0:
        print(f"Error running the attestation experiments: {output.stderr}")

    lines = output.stdout.split("\n")
    with open(outputdir_host / "attestation_results.log", "w") as f:
        f.write("\n".join(lines))

    """
    Gather the verification measurements.
    """
    verification_script = (
        f"{PROJECT_ROOT}/benchmarks/attestation/tdx/measure_quote_verification.sh"
    )
    print(verification_script)
    try:
        # Run the verification script and capture its output
        result = subprocess.run(
            [verification_script], capture_output=True, text=True, check=True
        )

        # Append the verification results to the output file
        with open(outputdir_host / "attestation_results.log", "a") as f:
            f.write(result.stdout)
            f.write("\n")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")
        print(f"Error output: {e.stderr}")

    print(f"Results saved in {outputdir_host}")
