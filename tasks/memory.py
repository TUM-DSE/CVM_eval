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


def parse_mlc_result(base_dir: Path, date: Optional[str] = None):
    """Parse the mlc result and return a DataFrame

    Exmaple:

    Intel(R) Memory Latency Checker - v3.11a
    *** Unable to modify prefetchers (try executing 'modprobe msr')
    *** So, enabling random access for latency measurements
    Measuring idle latencies for random access (in ns)...
                Numa node
    Numa node	     0
           0	 103.4

    Measuring Peak Injection Memory Bandwidths for the system
    Bandwidths are in MB/sec (1 MB/sec = 1,000,000 Bytes/sec)
    Using all the threads from each core if Hyper-threading is enabled
    Using traffic with the following read-write ratios
    ALL Reads        :	97902.9
    3:1 Reads-Writes :	108308.3
    2:1 Reads-Writes :	107110.1
    1:1 Reads-Writes :	97476.6
    Stream-triad like:	108632.0
    """

    if date is None:
        date = sorted([d for d in base_dir.iterdir() if d.is_dir()])[-1].name
    result_file = base_dir / date / "mlc.log"

    # XXX: this assumes one NUMA node environment!

    # extract idle latencies and peak injeciton memory bandwidth
    with open(result_file, "r") as f:
        lines = f.readlines()
        idle_latencies = []
        peak_bandwidths = []
        for i, line in enumerate(lines):
            if line.startswith("Measuring idle latencies"):
                idle_latencies = float(lines[i + 3].strip().split("\t")[1])
            if line.startswith("Measuring Peak Injection Memory Bandwidths"):
                peak_bandwidths = [
                    float(l.strip().split("\t")[1]) for l in lines[i + 4 : i + 9]
                ]

    return idle_latencies, np.array(peak_bandwidths)


@task
def show_mlc_result(cx: Any, cvm: str = "snp", size: str = "medium", tmebypass: bool = False):
    p = ""
    if cvm == "snp":
        vm = "amd"
    else:
        vm = "intel"
        if tmebypass:
            p = "-tmebypass"

    RESULT_DIR = PROJECT_ROOT / f"bench-result/memory/mlc"

    vm_lat, vm_bw = parse_mlc_result(RESULT_DIR / f"{vm}-direct-{size}{p}")
    cvm_lat, cvm_bw = parse_mlc_result(RESULT_DIR / f"{cvm}-direct-{size}")

    print(f"{vm},{vm_lat},{vm_bw}")
    print(f"{cvm},{cvm_lat},{cvm_bw}")

    print(f"lat diff: {cvm_lat - vm_lat:.3f}")
    bw_overhead = cvm_bw / vm_bw
    percent_overhead = (1 - bw_overhead) * 100
    geomean = np.prod(bw_overhead) ** (1 / len(bw_overhead))
    overhead = (1 - geomean) * 100
    geomen_bw_overhead = np.prod(bw_overhead) ** (1 / len(bw_overhead))
    print(percent_overhead)
    print((1-geomen_bw_overhead)*100)
    print(f"bw diff: {bw_overhead}, {geomean:.3f}, {overhead:.3f}%")


@task
def show_mmap_result(cx: Any, cvm: str = "snp", size: str = "medium", tmebypass: bool = False):
    """Parse mmap measure log and show the result"""
    p = ""
    if cvm == "snp":
        vm = "amd"
    else:
        vm = "intel"
        if tmebypass:
            p = "-tmebypass"

    RESULT_DIR = PROJECT_ROOT / f"bench-result/memory/mmap-time"

    for v in [vm, cvm]:
        for n in ["1st", "2nd"]:
            if v == vm:
                log = RESULT_DIR / f"{v}-direct-{size}{p}/{n}.txt"
            else:
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
