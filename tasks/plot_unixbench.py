#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
from typing import Any, Dict, List, Union, Optional
import pandas as pd
import os
import numpy as np
from pathlib import Path

from invoke import task

import phoronix

# common graph settings

mpl.use("Agg")
mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "libertine"

sns.set_style("whitegrid")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
sns.set_context("paper", rc={"font.size": 5, "axes.titlesize": 5, "axes.labelsize": 8})

# 3.3 inch for single column, 7 inch for double column
figwidth_half = 3.3
figwidth_full = 7

FONTSIZE = 9

pastel = sns.color_palette("pastel")
vm_col = pastel[0]
cvm_col = pastel[2]
palette = [vm_col, cvm_col]
hatches = ["", "//"]

BENCH_RESULT_DIR = Path("./bench-result/unixbench/")

BENHCMARK_NAME = [
    "Dhrystone 2 using register variables",
    "Double-Precision Whetstone",
    "Execl Throughput",
    "File Copy 1024 bufsize 2000 maxblocks",
    "File Copy 256 bufsize 500 maxblocks",
    "File Copy 4096 bufsize 8000 maxblocks",
    "Pipe Throughput",
    "Pipe-based Context Switching",
    "Process Creation",
    "Shell Scripts (1 concurrent)",
    "Shell Scripts (8 concurrent)",
    "System Call Overhead",
]

SHORT_NAME = [
    "Dhrystone",
    "Whetstone",
    "Exel",
    "File-mid",
    "File-small",
    "File-large",
    "Pipe",
    "Context-switch",
    "Process",
    "Scripts-1",
    "Scripts-8",
    "Syscall",
]


def parse_result(type: str, name: str, date: Optional[str] = None) -> pd.DataFrame:
    """Example format
    System Benchmarks Index Values               BASELINE       RESULT    INDEX
    Dhrystone 2 using register variables         116700.0  263721433.8  22598.2
    Double-Precision Whetstone                       55.0      39234.1   7133.5
    Execl Throughput                                 43.0      20736.3   4822.4
    File Copy 1024 bufsize 2000 maxblocks          3960.0   10207871.1  25777.5
    File Copy 256 bufsize 500 maxblocks            1655.0    2950460.3  17827.6
    File Copy 4096 bufsize 8000 maxblocks          5800.0   27915051.7  48129.4
    Pipe Throughput                               12440.0   15274023.1  12278.2
    Pipe-based Context Switching                   4000.0    1954459.3   4886.1
    Process Creation                                126.0      47407.7   3762.5
    Shell Scripts (1 concurrent)                     42.4      19512.3   4602.0
    Shell Scripts (8 concurrent)                      6.0       2887.3   4812.2
    System Call Overhead                          15000.0   13710090.9   9140.1
    """

    path = BENCH_RESULT_DIR / name
    if date is None:
        files = os.listdir(path)
        # remove if file contains extension (e.g., .html)
        files = [f for f in files if "." not in f and Path(path / f).is_file()]
        date = sorted(files)[-1]
    path = path / date

    print(path)

    # parse file
    with open(path, "r") as f:
        lines = f.readlines()
        # find "System Benchmarks Index Values" line from the end
        for i, line in enumerate(reversed(lines)):
            if "System Benchmarks Index Values" in line:
                break
        lines = lines[-i:]

        data = []
        for line in lines:
            # find line that starts with any of BENCHMARKNAME
            for i, bench in enumerate(BENHCMARK_NAME):
                if line.startswith(bench):
                    results = line[len(bench) :].strip().split()
                    index = float(results[2]) / 1000
                    data.append(
                        {"type": type, "benchmark": SHORT_NAME[i], "index": index}
                    )
                    break

    df = pd.DataFrame(data)

    return df


@task
def plot_unixbench(
    ctx: Any,
    cvm: str = "snp",
    outdir: str = "./plot",
    outname: str = "unixbench",
    size: str = "medium",
    disk: str = "nvme1n1",
    rel: bool = True,
    tmebypass: bool = False,
    result_dir=None,
):
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    p = ""
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        if tmebypass:
            p = "-tmebpass"

    vm_df = parse_result(vm_label, f"{vm}-direct-{size}-{disk}{p}")
    cvm_df = parse_result(cvm_label, f"{cvm}-direct-{size}-{disk}")
    # cvm_poll_df = parse_result(f"{cvm_label}-poll", f"{cvm}-direct-{size}-{disk}-poll")

    df = pd.concat([vm_df, cvm_df])

    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))

    sns.barplot(
        data=df,
        x="benchmark",
        y="index",
        hue="type",
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_xticklabels(SHORT_NAME, fontsize=5, rotation=30, ha="right")
    # ax.set_xticklabels(SHORT_NAME, fontsize=5)
    ax.set_ylabel("Benchmark Index [K]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # calculate relative values for each benchmark
    # type vm is the baseline
    vm_index = vm_df["index"].values
    cvm_index = cvm_df["index"].values
    relative = cvm_index / vm_index

    # print relative numbers
    print(relative)
    # report geometric mean of relative velues
    geometric_mean = np.prod(relative) ** (1 / len(relative))
    overhead = (1 - geometric_mean) * 100
    print(f"Geometric mean of relative values: {geometric_mean}")
    print(f"Overhead: {overhead:.2f}%")

    # calc geomean of exel and process
    exel = relative[2]
    process = relative[8]
    geomean = (exel * process) ** (1 / 2)
    overhead = (1 - geomean) * 100
    print(f"Geometric mean of Exel and Process: {geomean}")
    print(f"Overhead: {overhead:.2f}%")

    others = relative[[0, 1, 3, 4, 5, 6, 7, 9, 10, 11]]
    geomean = np.prod(others) ** (1 / len(others))
    overhead = (1 - geomean) * 100
    print(f"Geometric mean of other benchmarks: {geomean}")
    print(f"Overhead: {overhead:.2f}%")

    if rel:
        # plot relative values using the right axis
        ax2 = ax.twinx()
        ax2.plot(
            SHORT_NAME,
            relative,
            marker="o",
            color="gray",
            label="Relative",
            markersize=1,
        )
        ax2.set_ylabel("Relative Performance", color="black", fontsize=5)
        ax2.tick_params(axis="y", labelcolor="black")
        # ax2.set_ylim([0, 1.5])
        ax2.set_ylim([0.8, 1.1])
        # draw 1.0 line
        ax2.axhline(y=1.0, color="black", linestyle="--", linewidth=0.5)
        # ax2.legend(loc="best"h)

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = len(SHORT_NAME)
    for hatch in hatches:
        hs.extend([hatch] * num_x)
    num_legend = len(bars) - len(hs)
    hs.extend([""] * num_legend)
    for bar, hatch in zip(bars, hs):
        bar.set_hatch(hatch)

    # set hatch for the legend
    for patch in ax.get_legend().get_patches()[1::2]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=5, rotation=90)

    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if not rel:
        save_path = outdir / f"{outname}_{size}_{disk}_norel.pdf"
    else:
        save_path = outdir / f"{outname}_{size}_{disk}.pdf"
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")
