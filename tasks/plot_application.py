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
hatches2 = ["", "", "//"]

BENCH_RESULT_DIR = Path("./bench-result/application")


# bench mark path:
# ./bench-result/application/blender/{name}/{date}/
def parse_blender_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "blender" / name))[-1]
    path = BENCH_RESULT_DIR / "blender" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    print(f"{path}")

    # iterate over the files in the directory
    times = []
    for file in os.listdir(path):
        with open(path / file) as f:
            lines = f.readlines()
        # find a line starting with "Time:"
        for line in lines:
            if line.startswith("Time:"):
                # example format:
                # Time: 00:02.97 (Saving: 00:00.07)
                time = line.split()[1]
                # convert to seconds
                minutes, seconds = time.split(":")
                times.append(int(minutes) * 60 + float(seconds))
                break
        else:
            print(f"XXX: No time found in {file}")
            continue

    if len(times) == 0:
        return 0

    # return median value
    return np.median(times)


def parse_pytorch_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "pytorch" / name))[-1]
    path = BENCH_RESULT_DIR / "pytorch" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    print(f"{path}")

    # iterate over the files in the directory
    times = []
    for file in os.listdir(path):
        with open(path / file) as f:
            lines = f.readlines()
        # find a line starting with "Time:"
        for line in lines:
            if line.startswith("Time:"):
                # example format:
                # Time: 7.30 seconds
                time = float(line.split(":")[1].strip().split()[0])
                times.append(time)
                break
        else:
            print(f"XXX: No time found in {file}")
            continue

    if len(times) == 0:
        return 0

    # return median value
    return np.median(times)


def parse_tensorflow_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "tensorflow" / name))[-1]
    path = BENCH_RESULT_DIR / "tensorflow" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    print(f"{path}")

    # iterate over the files in the directory
    times = []
    for file in os.listdir(path):
        with open(path / file) as f:
            lines = f.readlines()
        # find a line starting with "Total throughput"
        for line in lines:
            if line.startswith("Total throughput"):
                # example format:
                # Total throughput (examples/sec): 9.26154306852012
                time = float(line.split(":")[1].strip())
                times.append(time)
                break
        else:
            print(f"XXX: No time found in {file}")
            continue

    if len(times) == 0:
        return 0

    # return median value
    return np.median(times)


# bench mark path:
# ./bench-result/application/sqlite/{name}/{date}/
def parse_sqlite_result(
    name: str, date: Optional[str] = None, label: Optional[str] = None
) -> pd.DataFrame:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "sqlite" / name))[-1]
    if label is None:
        label = name
    path = BENCH_RESULT_DIR / "sqlite" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    print(f"{path}")

    workloads = ["seq", "rand", "update", "update_rand"]

    # create data frame like
    # | name | workload | time |

    # iterate over the files in the directory
    rows = []
    for workload in workloads:
        path = BENCH_RESULT_DIR / "sqlite" / name / date / f"{workload}.log"
        with open(path) as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("Total elapsed time:"):
                time = float(line.split(":")[1].strip())
                rows.append({"name": label, "workload": workload, "time": time})
                break
        else:
            print(f"XXX: No time found in {file}")
            continue

    df = pd.DataFrame(rows, columns=["name", "workload", "time"])

    return df


@task
def plot_application(
    ctx,
    cvm="snp",
    outdir="plot",
    outname="application.pdf",
    sizes=[],
    labels=[],
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    if len(sizes) == 0:
        sizes = ["small", "medium", "large", "numa"]
        labels = ["small", "medium", "large", "xlarge"]

    # create a data frame like
    # | VM | Size | Application | Time |
    # |----|------|-------------|------|
    # |    |      |             |      |
    data = []
    for vmname, vmlabel in zip([vm, cvm], [vm_label, cvm_label]):
        for size, label in zip(sizes, labels):
            data.append(
                {
                    "VM": vmlabel,
                    "Size": label,
                    "Application": "Blender",
                    "Time": parse_blender_result(f"{vmname}-direct-{size}"),
                },
            )
            data.append(
                {
                    "VM": vmlabel,
                    "Size": label,
                    "Application": "Tensorflow",
                    "Time": parse_tensorflow_result(f"{vmname}-direct-{size}"),
                },
            )
            data.append(
                {
                    "VM": vmlabel,
                    "Size": label,
                    "Application": "Pytorch",
                    "Time": parse_pytorch_result(f"{vmname}-direct-{size}"),
                },
            )
    df = pd.DataFrame(data)
    print(df)

    fig, ax = plt.subplots(1, 3, figsize=(figwidth_full, 2.0), sharey=False)
    sns.barplot(
        data=df[df["Application"] == "Blender"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[0],
        palette=palette,
        edgecolor="black",
    )
    sns.barplot(
        data=df[df["Application"] == "Pytorch"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[1],
        palette=palette,
        edgecolor="black",
    )
    sns.barplot(
        data=df[df["Application"] == "Tensorflow"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[2],
        palette=palette,
        edgecolor="black",
    )

    # set hatch
    # note: we should set hatch before removing legends (if do so)
    for i in range(3):
        bars = ax[i].patches
        hs = []
        num_x = len(df["Size"].unique())
        for hatch in hatches:
            hs.extend([hatch] * num_x)
        num_legend = len(bars) - len(hs)
        hs.extend([""] * num_legend)
        for bar, hatch in zip(bars, hs):
            bar.set_hatch(hatch)
    # set hatch for the legend
    for patch in ax[0].get_legend().get_patches()[1::2]:
        patch.set_hatch("//")

    ax[0].set_title("Blender (Lower is better ↓)", fontsize=FONTSIZE, color="navy")
    ax[1].set_title("Pytorch (Lower is better ↓)", fontsize=FONTSIZE, color="navy")
    ax[2].set_title("Tensorflow (Higher is better ↑)", fontsize=FONTSIZE, color="navy")

    ax[0].set_ylabel("Time (s)")
    ax[1].set_ylabel("Time (s)")
    ax[2].set_ylabel("Throughput (examples/s)")

    # remove xlabel
    ax[0].set_xlabel("")
    ax[1].set_xlabel("")
    ax[2].set_xlabel("")

    # remove legend
    ax[1].get_legend().remove()
    ax[2].get_legend().remove()
    # remove lengend title
    ax[0].get_legend().set_title("")

    # annotate values with .2f
    for i in range(3):
        for container in ax[i].containers:
            # if the value is 0, put N/A
            for bar in container:
                if bar.get_height() < 1e-6:
                    txt = "N/A"
                    xy = (bar.get_x() + bar.get_width() / 2, 0)
                else:
                    txt = f"{bar.get_height():.2f}"
                    xy = (bar.get_x() + bar.get_width() / 2, bar.get_height())
                ax[i].annotate(
                    txt,
                    xy=xy,
                    xytext=(0, 1),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=5,
                )

    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_sqlite(
    ctx,
    cvm="snp",
    outdir="plot",
    outname="sqlite",
    size="medium",
    aio="native",
    device="nvme0n1",
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    vm_df = parse_sqlite_result(f"{vm}-direct-{size}{device}-{aio}", label=vm_label)
    swiotlb_df = parse_sqlite_result(f"{vm}-direct-{size}{device}-{aio}-swiotlb",
                                     label="swiotlb")
    cvm_df = parse_sqlite_result(f"{cvm}-direct-{size}{device}-{aio}", label=cvm_label)
    df = pd.concat([vm_df, swiotlb_df, cvm_df])

    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="time",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Runtime [sec]")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = 4
    for hatch in hatches2:
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
    save_path = outdir / f"{outname}_{device}.pdf"
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")
