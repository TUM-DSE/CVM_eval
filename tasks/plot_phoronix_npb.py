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

palette = sns.color_palette("pastel")
hatches = ["", "//"]

BENCHMARK_ID = [
    "NAS Parallel Benchmarks: Test / Class: BT.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: CG.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: EP.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: EP.D [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: FT.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: IS.D [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: LU.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: MG.C [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: SP.B [Total Mop/s]",
    "NAS Parallel Benchmarks: Test / Class: SP.C [Total Mop/s]",
]


LABELS = [
    "BT.C",
    "CG.C",
    "EP.C",
    "EP.D",
    "FT.C",
    "IS.D",
    "LU.C",
    "MG.C",
    "SP.B",
    "SP.C",
]

assert len(BENCHMARK_ID) == len(LABELS)

palette = sns.color_palette("pastel")

BENCH_RESULT_DIR = Path("./bench-result/phoronix/")


def parse_result(name: str, date: Optional[str] = None) -> pd.DataFrame:
    if date is None:
        date = sorted(os.listdir(BENCH_RESULT_DIR / name / "npb"))[-1]
    path = BENCH_RESULT_DIR / name / "npb" / date

    df = phoronix.parse_xml(path)
    return df


def load_data(vm: str, cvm: str, rel=True, size="large") -> pd.DataFrame:
    vm_df = parse_result(f"{vm}-direct-{size}")
    cvm_df = parse_result(f"{cvm}-direct-{size}")

    if not rel:
        df = pd.concat([vm_df, cvm_df])
        return df

    # merge two using identifier and benchmark_id as a key
    data = pd.merge(vm_df, cvm_df, on="benchmark_id", suffixes=(f"_{vm}", f"_{cvm}"))
    data["relative"] = data[f"value_{cvm}"] / data[f"value_{vm}"]

    # drop rows if its benchmark_id is not in BENCHMARK_ID
    data = data[data["benchmark_id"].isin(BENCHMARK_ID)]

    data.sort_values(
        by="benchmark_id",
        inplace=True,
        key=lambda x: [BENCHMARK_ID.index(i) for i in x],
    )

    data.reset_index(drop=True, inplace=True)

    return data


@task
def plot_npb_rel(
    ctx: Any,
    vm: str = "amd",
    cvm: str = "snp",
    outdir: str = "./plot",
    name: str = "npb_rel.pdf",
):
    data = load_data(vm, cvm)

    # fig, ax = plt.subplots(figsize=(4.5, 4.0))
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))

    ax.barh(
        data["benchmark_id"],
        data["relative"],
        color=palette,
        edgecolor="black",
        label=cvm,
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
    print(f"Plot saved in {outpath}")


@task
def plot_npb(
    ctx: Any,
    vm: str = "amd",
    cvm: str = "snp",
    outdir: str = "./plot",
    outname: str = "npb.pdf",
    size: str = "large",
):
    df = load_data(vm, cvm, rel=False, size=size)
    df["identifier"] = df["identifier"].map(
        {f"{vm}-direct-{size}": vm, f"{cvm}-direct-{size}": cvm}
    )
    df["benchmark_id"] = df["benchmark_id"].map(
        {i: j for i, j in zip(BENCHMARK_ID, LABELS)}
    )
    df["value"] = df["value"] / 1e3  # convert to G op/s
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))

    sns.barplot(
        data=df,
        x="benchmark_id",
        y="value",
        hue="identifier",
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_xticklabels(LABELS, fontsize=5)
    ax.set_ylabel("Throughput [G op/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = len(LABELS)
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
        ax.bar_label(container, fmt="%.2f")

    plt.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")
