#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
from typing import Any, Dict, List, Union
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

palette = sns.color_palette("pastel")
hatches = ["", "//"]

BENCHMARK_ID = [
    "Stream: Type: Copy [MB/s]",
    "Stream: Type: Scale [MB/s]",
    "Stream: Type: Triad [MB/s]",
    "Stream: Type: Add [MB/s]",
    "RAMspeed SMP: Type: Add - Benchmark: Integer [MB/s]",
    "RAMspeed SMP: Type: Copy - Benchmark: Integer [MB/s]",
    "RAMspeed SMP: Type: Scale - Benchmark: Integer [MB/s]",
    "RAMspeed SMP: Type: Triad - Benchmark: Integer [MB/s]",
    "RAMspeed SMP: Type: Average - Benchmark: Integer [MB/s]",
    "RAMspeed SMP: Type: Add - Benchmark: Floating Point [MB/s]",
    "RAMspeed SMP: Type: Copy - Benchmark: Floating Point [MB/s]",
    "RAMspeed SMP: Type: Scale - Benchmark: Floating Point [MB/s]",
    "RAMspeed SMP: Type: Triad - Benchmark: Floating Point [MB/s]",
    "RAMspeed SMP: Type: Average - Benchmark: Floating Point [MB/s]",
    # "MBW: Test: Memory Copy - Array Size: 128 MiB [MiB/s]",
    # "MBW: Test: Memory Copy - Array Size: 512 MiB [MiB/s]",
    "MBW: Test: Memory Copy - Array Size: 1024 MiB [MiB/s]",
    # "MBW: Test: Memory Copy - Array Size: 4096 MiB [MiB/s]",
    # "MBW: Test: Memory Copy, Fixed Block Size - Array Size: 128 MiB [MiB/s]",
    # "MBW: Test: Memory Copy, Fixed Block Size - Array Size: 512 MiB [MiB/s]",
    "MBW: Test: Memory Copy, Fixed Block Size - Array Size: 1024 MiB [MiB/s]",
    # "MBW: Test: Memory Copy, Fixed Block Size - Array Size: 4096 MiB [MiB/s]",
    "Tinymembench: Standard Memcpy [MB/s]",
    "Tinymembench: Standard Memset [MB/s]",
    "t-test1: Threads: 1 [Seconds]",
    "t-test1: Threads: 2 [Seconds]",
    "CacheBench: Read Cache [MB/s]",
    "CacheBench: Write Cache [MB/s]",
]

# "CacheBench: Test: Read [MB/s]",
# "CacheBench: Test: Write [MB/s]",
# "CacheBench: Test: Read / Modify / Write [MB/s]",

LABELS = [
    "Stream (Copy)",
    "Stream (Scale)",
    "Stream (Triad)",
    "Stream (Add)",
    "RAMspeed (Add Int)",
    "RAMspeed (Copy Int)",
    "RAMspeed (Scale Int)",
    "RAMspeed (Triad Int)",
    "RAMspeed (Average Int)",
    "RAMspeed (Add FP)",
    "RAMspeed (Copy FP)",
    "RAMspeed (Scale FP)",
    "RAMspeed (Triad FP)",
    "RAMspeed (Average FP)",
    # "MBW (Copy 128MB)",
    # "MBW (Copy 512 MiB)",
    "MBW (Copy 1024 MiB)",
    # "MBW (Copy 4096 MiB)",
    # "MBW (Copy Fix 128MB)",
    # "MBW (Copy Fixed 512 MiB)",
    "MBW (Copy Fixed 1024 MiB)",
    # "MBW (Copy Fixed 4096 MiB)",
    "Tinymembench (Memcpy)",
    "Tinymembench (Memset)",
    "t-test1 Threads: 1",
    "t-test1 Threads: 2",
    "CacheBench (R)",
    "CacheBench (W)",
]

assert len(BENCHMARK_ID) == len(LABELS)

palette = [
    *(palette[0] for _ in list(range(4))),  # stream
    *(palette[1] for _ in list(range(10))),  # ramspeed
    *(palette[2] for _ in list(range(2))),  # mbw
    *(palette[3] for _ in list(range(2))),  # tinymembench
    *(palette[4] for _ in list(range(2))),  # t-test1
    *(palette[5] for _ in list(range(2))),  # cachebench
]


def load_data(vmfile: Path, snpfile: Path) -> pd.DataFrame:
    vm = phoronix.parse_xml(vmfile)
    snp = phoronix.parse_xml(snpfile)

    # merge two using identifier and benchmark_id as a key
    data = pd.merge(vm, snp, on="benchmark_id", suffixes=("_vm", "_snp"))
    data["relative"] = data["value_snp"] / data["value_vm"]

    data.sort_values(
        by="benchmark_id",
        inplace=True,
        key=lambda x: [BENCHMARK_ID.index(i) for i in x],
    )

    data.reset_index(drop=True, inplace=True)

    return data


@task
def plot_phoronix_memory(
    ctx: Any, vmfile: str, snpfile: str, outdir: str = "./", name: str = "memory.pdf"
):
    data = load_data(Path(vmfile), Path(snpfile))

    # fig, ax = plt.subplots(figsize=(4.5, 4.0))
    fig, ax = plt.subplots()

    ax.barh(
        data["benchmark_id"],
        data["relative"],
        color=palette,
        edgecolor="black",
        label="SNP",
    )

    # draw a line at 1.0 to indicate the baseline
    ax.axvline(x=1, color="black", linestyle="--", linewidth=0.5)

    # annotate values
    for container in ax.containers:
        ax.bar_label(container, fontsize=5, fmt="%.2f", padding=2)

    # change ylabels
    ax.set_yticklabels(LABELS, fontsize=5)

    # set hatch
    # bars = ax.patches
    # hs = []
    # for h in hatches:
    #     for i in range(int(len(bars) / len(hatches))):
    #         hs.append(h)
    # for bar, hatch in zip(bars, hs):
    #     bar.set_hatch(hatch)

    ax.set_xlabel("Relative value")
    ax.set_ylabel("")

    ax.set_title("Higher is better →", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    plt.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True, parents=True)
    outpath = outdir / name
    plt.savefig(outpath, format="pdf", pad_inches=0, bbox_inches="tight")
