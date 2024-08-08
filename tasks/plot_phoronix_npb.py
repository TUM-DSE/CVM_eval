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
from matplotlib.patches import Patch

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
hatches = ["", "//", "\\", "x"]

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

BENCH_RESULT_DIR = Path("./bench-result/phoronix/")


def parse_result(name: str, date: Optional[str] = None) -> pd.DataFrame:
    if date is None:
        date = sorted(os.listdir(BENCH_RESULT_DIR / name / "npb"))[-1]
    path = BENCH_RESULT_DIR / name / "npb" / date

    df = phoronix.parse_xml(path)
    return df


def load_data(
    vm: str, cvm: str, rel=True, size="numa", pvm="", pcvm=""
) -> pd.DataFrame:
    vm_df = parse_result(f"{vm}-direct-{size}{pvm}")
    cvm_df = parse_result(f"{cvm}-direct-{size}{pcvm}")

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
    cvm: str = "snp",
    outdir: str = "./plot",
    name: str = "npb_rel.pdf",
):
    if cvm == "snp":
        vm = "amd"
        cvm_label = "snp"
    else:
        vm = "intel"
        cvm_label = "td"

    data = load_data(vm, cvm)

    # fig, ax = plt.subplots(figsize=(4.5, 4.0))
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))

    ax.barh(
        data["benchmark_id"],
        data["relative"],
        color=palette,
        edgecolor="black",
        label=cvm_label,
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
    sns.despine(top = True)
    plt.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(exist_ok=True, parents=True)
    outpath = outdir / name
    plt.savefig(outpath, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"Plot saved in {outpath}")


@task
def plot_npb(
    ctx: Any,
    cvm: str = "snp",
    outdir: str = "./plot",
    outname: str = "npb",
    size: str = "medium",
    rel: bool = True,
    tmebypass: bool = False,
    poll: bool = False,
    result_dir=None,
):
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    pcvm = ""
    pvm = ""
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
    df = load_data(vm, cvm, rel=False, size=size, pvm=pvm, pcvm=pcvm)
    df["identifier"] = df["identifier"].map(
        {f"{vm}-direct-{size}{pvm}": vm_label, f"{cvm}-direct-{size}{pcvm}": cvm_label}
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

    # calculat relative values for each benchmark
    # type vm is the baseline
    vm_index = df[df["identifier"] == vm_label]["value"].values
    cvm_index = df[df["identifier"] == cvm_label]["value"].values
    relative = cvm_index / vm_index
    print(relative)
    # geomean
    geomean = np.exp(np.mean(np.log(relative)))
    overhead = (1 - geomean) * 100
    print(f"Geometric mean of relative values: {geomean}")
    print(f"Overhead: {overhead:.2f}%")

    if rel:
        # plot rel using right axis
        ax2 = ax.twinx()
        ax2.plot(
            LABELS,
            relative,
            color="gray",
            marker="o",
            markersize=1,
            label="Relative",
        )
        ax2.set_ylabel("Relative value", fontsize=5)
        ax2.set_ylim(0.8, 1.1)
        ax2.axhline(y=1, color="black", linestyle="--", linewidth=0.5)

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
    if not rel:
        save_path = outdir / f"{outname}_{size}_norel{pvm}.pdf"
    else:
        save_path = outdir / f"{outname}_{size}{pvm}.pdf"
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


# -----------------


def extract_time_from_log(file_path):
    with open(file_path, "r") as file:
        for line in file:
            if "Time in seconds =" in line:
                return float(line.split("=")[1].strip())
    return None


def get_wait_policy(file_name):
    if "passive" in file_name:
        return "passive"
    elif "active" in file_name:
        return "active"
    else:
        return "default"


def parse_experiment_results(root_dir, type=None):
    data = []

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".log"):
                parts = file.split(".")
                benchmark = parts[0]
                size = parts[1]
                wait_policy = get_wait_policy(file)
                time = extract_time_from_log(os.path.join(root, file))

                dir_parts = root.split(os.sep)
                if type is None:
                    type = dir_parts[-1]  # get the last part of the path

                data.append(
                    {
                        "type": type,
                        "benchmark": benchmark,
                        "size": size,
                        "wait_policy": wait_policy,
                        "time": time,
                    }
                )

    df = pd.DataFrame(data)
    return df


def plot_execution_times(df, size="C", outdir="./plot"):
    # Filter the DataFrame for size 'C'
    df = df[df["size"] == size]

    # Get the unique wait policies
    wait_policies = df["wait_policy"].unique()

    # Create a plot for each wait policy
    for policy in wait_policies:
        df_policy = df[df["wait_policy"] == policy]

        plt.figure(figsize=(10, 6))
        ax = sns.barplot(
            data=df_policy,
            x="benchmark",
            y="time",
            hue="type",
            palette=pastel,
            edgecolor="black",
        )
        # set hatch
        # bars = ax.patches
        # hs = []
        # num_x = len(df_policy['benchmark'].unique())
        # hatches = ["", "//", "x", "o"]
        # for hatch in hatches:
        #    hs.extend([hatch] * num_x)
        # num_legend = len(bars) - len(hs)
        # hs.extend([""] * num_legend)
        # for bar, hatch in zip(bars, hs):
        #    bar.set_hatch(hatch)
        plt.title(f"Execution Time for Wait Policy: {policy}")
        plt.xlabel("Benchmark")
        plt.ylabel("Execution Time (seconds)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        plt.savefig(f"{outdir}/npb-omp_{size}_{policy}.pdf")


@task
def plot_npb_omp(
    ctx: Any,
    cvm: str = "snp",
    size: str = "large",
    npb_size: str = "C",
    outdir: str = "./plot",
    outname: str = "npb-omp",
    result_dir=None,
):
    if result_dir is None:
        result_dir = "./bench-result/npb-omp"
    result_dir = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    dfs = []
    dfs.append(parse_experiment_results(result_dir / f"{vm}-direct-{size}", vm_label))
    dfs.append(parse_experiment_results(result_dir / f"{cvm}-direct-{size}", cvm_label))
    df = pd.concat(dfs)

    # sort df using "type" and "benchmark"
    df = df.sort_values(by=["type", "benchmark"])
    df = df[df["size"] == npb_size]
    wait_policies = df["wait_policy"].unique()

    df['policy'] = df['type'] + '-' + df['wait_policy']
    df = df[df['wait_policy'] != 'default']
    print(df)

    vm_passive = df[(df['type'] == vm_label) & (df['wait_policy'] == 'passive')]
    cvm_passive = df[(df['type'] == cvm_label) & (df['wait_policy'] == 'passive')]
    vm_active = df[(df['type'] == vm_label) & (df['wait_policy'] == 'active')]
    cvm_active = df[(df['type'] == cvm_label) & (df['wait_policy'] == 'active')]

    # calculate the overhead of {cvm}-passive over {vm}-passive and {cvm}-active over {vm}-active for each benchmark
    ov_passive = []
    ov_active = []
    for benchmark in df['benchmark'].unique():
        vm_passive_time = vm_passive[vm_passive['benchmark'] == benchmark]['time'].values.mean()
        cvm_passive_time = cvm_passive[cvm_passive['benchmark'] == benchmark]['time'].values.mean()
        vm_active_time = vm_active[vm_active['benchmark'] == benchmark]['time'].values.mean()
        cvm_active_time = cvm_active[cvm_active['benchmark'] == benchmark]['time'].values.mean()

        overhead_passive = (cvm_passive_time - vm_passive_time) / vm_passive_time * 100
        overhead_active = (cvm_active_time - vm_active_time) / vm_active_time * 100
        ov_passive.append(overhead_passive)
        ov_active.append(overhead_active)
        #print(f"Overhead (passive) for {benchmark}: {overhead_passive}")
        #print(f"Overhead (active) for {benchmark}: {overhead_active}")
    ov_passive = np.array(ov_passive)
    ov_active = np.array(ov_active)
    print(f"Overhead (passive): {ov_passive}")
    print(f"Overhead (active): {ov_active}")

    # calculate geomen of overhead
    geomean_passive = np.exp(np.mean(np.log(ov_passive)))
    geomean_active = np.exp(np.mean(np.log(ov_active)))
    print(f"Geometric mean of overhead (passive): {geomean_passive}")
    print(f"Geometric mean of overhead (active): {geomean_active}")

    hue_order = [f"{vm_label}-passive", f"{cvm_label}-passive", f"{vm_label}-active", f"{cvm_label}-active"]
    palette = [vm_col, cvm_col, pastel[1], pastel[3]]

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    ax = sns.barplot(data=df, x='benchmark', y='time', hue='policy', ax=ax,
                     palette=palette, edgecolor="black", hue_order=hue_order)

    #hatches = ["", "//", "", "//"]
    hatches = ["", "//", "\\", "xx"]
    num_benchmark = len(df['benchmark'].unique())
    for i, hatch in enumerate(hatches):
        for j in range(num_benchmark):
            ax.patches[i * num_benchmark + j].set_hatch(hatch)


    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.02f", fontsize=5, rotation=90, padding=2)

    # Create custom legend
    handles = [
        Patch(facecolor=palette[i], edgecolor='black', hatch=hatches[i % len(hatches)], label=hue_order[i])
        for i in range(len(hue_order))
    ]

    # plt.title('NAS Parallel Benchmarks (OpenMP): Execution Time')
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    plt.xlabel('Benchmark')
    plt.ylabel('Execution Time [sec]')
    plt.legend(handles=handles, fontsize=7)
    sns.despine(top = True)
    plt.tight_layout()

    outfile = f"{outdir}/npb-omp_{npb_size}_{size}.pdf"
    plt.savefig(outfile)
    print(f"Plot saved in {outfile}")


