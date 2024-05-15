#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Any, Dict, List, Union

import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
from invoke import task
import pandas as pd
import numpy as np

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
hatches = ["", "//", "x"]

# bench mark path:
# ./bench-result/vmexit/{name}.txt
BENCH_RESULT_DIR = Path("./bench-result/vmexit")


def load_data(name):
    file = BENCH_RESULT_DIR / f"{name}.txt"
    start = -1
    with open(file) as f:
        lines = f.readlines()
        # find message "bench: Initializing" form the end
        for i, line in enumerate(reversed(lines)):
            if "bench: Initializing" in line:
                start = len(lines) - i
                break

    if start == -1:
        raise (f"Invalid format: {file}")

    # Example format
    # [  104.161314] bench: _cpuid_0, total_cycle 273468339, avg_cycle 2734, total_time 101286422, avg_time 1012
    # [  104.263563] bench: _cpuid_1, total_cycle 273312738, avg_cycle 2733, total_time 101228723, avg_time 1012

    results = {}
    for i in range(start, len(lines)):
        if "]" not in lines[i]:
            continue
        line = lines[i].split("]")[1]
        if "bench:" in line and "avg_time" in line:
            name = line.split(",")[0].strip().split()[1]
            avg_time = int(line.split(",")[4].strip().split()[1])
            results[name] = avg_time
        elif "bench: done" in line:
            break

    return results


@task
def plot_vmexit(ctx: Any, vm="amd", cvm="snp", outdir="plot"):
    vm_data = load_data(vm)
    cvm_data = load_data(cvm)
    print(vm_data)
    print(cvm_data)

    index = ["cpuid_1", "cpuid_40M", "msr", "hypercall", "inb"]
    vm_val = [
        vm_data["_cpuid_1"],
        vm_data["_cpuid_0x40000000"],
        vm_data["_rdmsr_0x1b"],
        vm_data["_hypercall_2"],
        vm_data["_inb_0x40"],
    ]
    cvm_val = [
        cvm_data["_cpuid_1"],
        cvm_data["_cpuid_0x40000000"],
        cvm_data["_rdmsr_0x1b"],
        cvm_data["_hypercall_2"],
        cvm_data["_inb_0x40"],
    ]
    cvm_opt_val = [
        cvm_data[f"{cvm}_cpuid_1"],
        cvm_data[f"{cvm}_cpuid_0x40000000"],
        cvm_data[f"{cvm}_rdmsr_0x1b"],
        cvm_data[f"{cvm}_hypercall_2"],
        cvm_data[f"{cvm}_inb_0x40"],
    ]

    data = pd.DataFrame(
        {f"{vm}": vm_val, f"{cvm}": cvm_val, f"{cvm}*": cvm_opt_val}, index=index
    )

    # create bar plot
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))
    data.plot(kind="bar", ax=ax, color=palette, edgecolor="black", fontsize=FONTSIZE)
    # annotate values
    for container in ax.containers:
        ax.bar_label(container, fontsize=5)
    # set hatch
    bars = ax.patches
    hs = []
    for h in hatches:
        for i in range(int(len(bars) / len(hatches))):
            hs.append(h)
    for bar, hatch in zip(bars, hs):
        bar.set_hatch(hatch)
    ax.set_ylabel("Time (ns)")
    ax.set_xlabel("")
    ax.set_xticklabels(data.index, rotation=0, fontsize=7)
    # ax.legend(loc="upper left", title=None, fontsize=FONTSIZE,
    #           bbox_to_anchor=(-0.02, 1.0))
    # place legend below the graph
    ax.legend(
        loc="upper center",
        title=None,
        fontsize=FONTSIZE,
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
    )
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    plt.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    plt.savefig(outdir / "vmexit.pdf", format="pdf", pad_inches=0, bbox_inches="tight")
