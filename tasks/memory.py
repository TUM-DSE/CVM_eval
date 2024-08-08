#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from subprocess import CalledProcessError

from invoke import task
import numpy as np
import pandas as pd

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


def parse_mlc_result_sub(name: str, file: Path):
    """
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

    # XXX: this assumes one NUMA node environment!

    # extract idle latencies and peak injeciton memory bandwidth
    with open(file, "r") as f:
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

    # create dataframe
    # | name | random_access_latency | bw_all_read | bw_3_1 | bw_2_1 | bw_1_1 | bw_stream |

    df = pd.DataFrame(
        {
            "name": [name],
            "random_access_latency": [idle_latencies],
            "bw_all_read": [peak_bandwidths[0]],
            "bw_3_1": [peak_bandwidths[1]],
            "bw_2_1": [peak_bandwidths[2]],
            "bw_1_1": [peak_bandwidths[3]],
            "bw_stream": [peak_bandwidths[4]],
        }
    )

    return df


def parse_mlc_result(
    label: str, base_dir: Path, date: Optional[str] = None, max_num: int = 10
):
    """Parse the mlc result and return a DataFrame"""

    fs = []
    if date is None:
        files = sorted([d for d in base_dir.iterdir() if d.is_dir()])[-10:]
        for f in files:
            fs.append(f / "mlc.log")
    else:
        fs.append(base_dir / date / "mlc.log")

    # parse file and create a dataframe
    dfs = []
    for f in fs:
        name = f.parent.name
        df = parse_mlc_result_sub(name, f)
        dfs.append(df)
    # concate result
    result = pd.concat(dfs, ignore_index=True)

    return result


@task
def show_mlc_result(
    cx: Any,
    cvm: str = "snp",
    size: str = "medium",
    tmebypass: bool = False,
    poll: bool = False,
    result_dir: Optional[str] = None,
):
    pvm = ""
    pcvm = ""
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        if tmebypass:
            pvm = "-tmebypass"
    if poll:
        pvm += "-poll"
        pcvm += "-poll"

    if result_dir is None:
        RESULT_DIR = PROJECT_ROOT / f"bench-result/memory/mlc"
    else:
        RESULT_DIR = Path(result_dir)

    vm_df = parse_mlc_result(vm_label, RESULT_DIR / f"{vm}-direct-{size}{pvm}")
    cvm_df = parse_mlc_result(cvm_label, RESULT_DIR / f"{cvm}-direct-{size}{pcvm}")

    print(vm_df)
    print(cvm_df)

    # latency difference (using median)
    vm_lat_median = vm_df["random_access_latency"].median()
    cvm_lat_median = cvm_df["random_access_latency"].median()
    print(
        f"random access latency: {vm_lat_median:.3f}, {cvm_lat_median:.3f}, {cvm_lat_median - vm_lat_median:.3f} us"
    )

    # bw overhead using median
    vm_bw = (
        vm_df[["bw_all_read", "bw_3_1", "bw_2_1", "bw_1_1", "bw_stream"]]
        .median()
        .values
    )
    cvm_bw = (
        cvm_df[["bw_all_read", "bw_3_1", "bw_2_1", "bw_1_1", "bw_stream"]]
        .median()
        .values
    )
    print(f"vm_bw: {vm_bw}")
    print(f"cvm_bw: {cvm_bw}")
    overhead = (1 - cvm_bw / vm_bw) * 100
    print(f"bw diff: {overhead}")
    geo_mean = np.prod(cvm_bw / vm_bw) ** (1 / len(cvm_bw))
    print(f"geomean: {geo_mean:.3f}, {(1 - geo_mean)*100:.3f}%")


@task
def show_mmap_result(
    cx: Any,
    cvm: str = "snp",
    size: str = "medium",
    tmebypass: bool = False,
    result_dir: Optional[str] = None,
):
    """Parse mmap measure log and show the result"""
    p = ""
    if cvm == "snp":
        vm = "amd"
    else:
        vm = "intel"
        if tmebypass:
            p = "-tmebypass"

    if result_dir is None:
        RESULT_DIR = PROJECT_ROOT / f"bench-result/memory/mmap-time"
    else:
        RESULT_DIR = Path(result_dir)

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

    for n in ["1st", "2nd"]:
        log = RESULT_DIR / f"{cvm}-direct-{size}-no-prealloc/{n}.txt"
        result = []
        with open(log, "r") as f:
            lines = f.readlines()
            result = [float(line) for line in lines]
        print(
            f"{cvm}-no-prealloc,{n},{np.median(result):.3f},{np.mean(result):.3f},{np.std(result):.3f}"
        )
