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
from utils import query_db
from tasks.plot_metrics import METRIC_FUNCS

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
swiotlb_col = pastel[1]
cvm_col = pastel[2]
poll_col = pastel[3]
hpoll_col = pastel[4]
palette = [vm_col, cvm_col]
palette2 = [vm_col, swiotlb_col, cvm_col]
palette3 = [vm_col, cvm_col, poll_col, hpoll_col]
hatches = ["", "//"]
hatches2 = ["", "", "//"]

BENCH_RESULT_DIR = Path("./bench-result/application")


def parse_blender_result_sub(name: str, file: Path):
    with open(file) as f:
        lines = f.readlines()
    # find a line starting with "Time:"
    for line in lines:
        if line.startswith("Time:"):
            # example format:
            # Time: 00:02.97 (Saving: 00:00.07)
            time = line.split()[1]
            # convert to seconds
            minutes, seconds = time.split(":")
            time = int(minutes) * 60 + float(seconds)

    # create df
    # | name | time |
    df = pd.DataFrame({"name": [name], "time": [time]})
    return df


# bench mark path:
# ./bench-result/application/blender/{name}/{date}/
def parse_blender_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "blender" / name))[-1]
    path = BENCH_RESULT_DIR / "blender" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        raise FileNotFoundError

    # iterate over the files in the directory
    dfs = []
    for file in os.listdir(path):
        df = parse_blender_result_sub(name, path / file)
        dfs.append(df)

    # merge dfs
    df = pd.concat(dfs, ignore_index=True)

    return df


def parse_pytorch_result_sub(name: str, file: Path):
    with open(file) as f:
        lines = f.readlines()
    # find a line starting with "Time:"
    for line in lines:
        if line.startswith("Time:"):
            # example format:
            # Time: 7.30 seconds
            time = float(line.split(":")[1].strip().split()[0])
            # create df
            # | name | time |
            df = pd.DataFrame({"name": [name], "time": [time]})
            return df

    print(f"XXX: No time found in {file}")
    raise FileNotFoundError


def parse_pytorch_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "pytorch" / name))[-1]
    path = BENCH_RESULT_DIR / "pytorch" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    # iterate over the files in the directory
    dfs = []
    for file in os.listdir(path):
        df = parse_pytorch_result_sub(name, path / file)
        dfs.append(df)

    # merge dfs
    df = pd.concat(dfs, ignore_index=True)

    return df


def parse_tensorflow_result_sub(name: str, file: Path):
    with open(file) as f:
        lines = f.readlines()
    # find a line starting with "Total throughput"
    for line in lines:
        if line.startswith("Total throughput"):
            # example format:
            # Total throughput (examples/sec): 9.26154306852012
            time = float(line.split(":")[1].strip())
            # create df
            # | name | time |
            df = pd.DataFrame({"name": [name], "time": [time]})
            return df

    print(f"XXX: No time found in {file}")
    raise FileNotFoundError


def parse_tensorflow_result(name: str, date: Optional[str] = None) -> float:
    if date is None:
        # we use the latest result if date is not provided
        date = sorted(os.listdir(BENCH_RESULT_DIR / "tensorflow" / name))[-1]
    path = BENCH_RESULT_DIR / "tensorflow" / name / date

    if not os.path.exists(path):
        print(f"XXX: No result found in {path}")
        return 0

    # iterate over the files in the directory
    dfs = []
    for file in os.listdir(path):
        df = parse_tensorflow_result_sub(name, path / file)
        dfs.append(df)
    if len(dfs) == 0:
        dfs.append(pd.DataFrame({"name": [name], "time": [0]}))

    # merge dfs
    df = pd.concat(dfs, ignore_index=True)

    return df


def parse_sqlite_result_sub(name: str, workload: str, file: Path):
    with open(file) as f:
        lines = f.readlines()
    # find a line starting with "Total elapsed time:"
    for line in lines:
        if line.startswith("Total elapsed time:"):
            time = float(line.split(":")[1].strip())
            # create df
            # | name | time |
            df = pd.DataFrame({"name": [name], "workload": [workload], "time": [time]})
            return df

    print(f"XXX: No time found in {file}")
    raise FileNotFoundError


# bench mark path:
# ./bench-result/application/sqlite/{name}/{date}/
def parse_sqlite_result(
    name: str,
    date: Optional[str] = None,
    label: Optional[str] = None,
    max_num: int = 10,
) -> pd.DataFrame:
    dates = []
    if date is None:
        # we use the latest results if date is not provided
        dates = sorted(os.listdir(BENCH_RESULT_DIR / "sqlite" / name))[:max_num]
    else:
        dates.append(date)
    if label is None:
        label = name

    workloads = ["seq", "rand", "update", "update_rand"]

    dfs = []
    for date in dates:
        path = BENCH_RESULT_DIR / "sqlite" / name / date
        if not os.path.exists(path):
            print(f"XXX: No result found in {path}")
            return 0
        for workload in workloads:
            file = path / f"{workload}.log"
            df = parse_sqlite_result_sub(label, workload, file)
            dfs.append(df)

    # merge dfs
    df = pd.concat(dfs, ignore_index=True)

    return df


@task
def plot_application(
    ctx,
    cvm="snp",
    outdir="plot",
    outname="application",
    sizes=[],
    labels=[],
    rel=True,
    tmebypass=False,
    poll=False,
    result_dir=None,
):
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
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

    if len(sizes) == 0:
        # labels = ["small", "medium", "large", "numa"]
        sizes = ["small", "medium", "large", "xlarge"]
        labels = ["S", "M", "L", "X"]

    # create a data frame like
    # | VM | Size | Application | Time |
    # |----|------|-------------|------|
    # |    |      |             |      |
    data = []
    for vmname, vmlabel, p in zip([vm, cvm], [vm_label, cvm_label], [pvm, pcvm]):
        for size, label in zip(sizes, labels):
            bl_df = parse_blender_result(f"{vmname}-direct-{size}{p}")
            for i, row in bl_df.iterrows():
                data.append(
                    {
                        "VM": vmlabel,
                        "Size": label,
                        "Application": "Blender",
                        "Time": row["time"],
                    },
                )
            tf_df = parse_tensorflow_result(f"{vmname}-direct-{size}{p}")
            for i, row in tf_df.iterrows():
                data.append(
                    {
                        "VM": vmlabel,
                        "Size": label,
                        "Application": "Tensorflow",
                        "Time": row["time"],
                    },
                )
            pt_df = parse_pytorch_result(f"{vmname}-direct-{size}{p}")
            for i, row in pt_df.iterrows():
                data.append(
                    {
                        "VM": vmlabel,
                        "Size": label,
                        "Application": "Pytorch",
                        "Time": row["time"],
                    },
                )
    df = pd.DataFrame(data)
    print(df)

    fig, ax = plt.subplots(1, 3, figsize=(figwidth_full, 1.7), sharey=False)
    sns.barplot(
        data=df[df["Application"] == "Blender"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[0],
        palette=palette,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    sns.barplot(
        data=df[df["Application"] == "Pytorch"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[1],
        palette=palette,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    sns.barplot(
        data=df[df["Application"] == "Tensorflow"],
        x="Size",
        y="Time",
        hue="VM",
        ax=ax[2],
        palette=palette,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )

    # calc relative values
    # type vm is the baseline
    for i, app in enumerate(["Blender", "Pytorch", "Tensorflow"]):
        # choose mean values of each size
        vm_mean = df[(df["VM"] == vm_label) & (df["Application"] == app)]
        vm_mean = vm_mean.groupby("Size")["Time"].mean()
        vm_index = np.array([vm_mean[label] for label in labels])
        cvm_mean = df[(df["VM"] == cvm_label) & (df["Application"] == app)]
        cvm_mean = cvm_mean.groupby("Size")["Time"].mean()
        cvm_index = np.array([cvm_mean[label] for label in labels])

        print("vm_index:", vm_index, cvm_index)

        if app == "Tensorflow":
            vm_index[0] = 1
            cvm_index[0] = 1
        relative = cvm_index / vm_index
        if i == 2:
            geoman = np.prod(relative[1:]) ** (1 / len(relative[1:]))
        else:
            geomean = np.exp(np.mean(np.log(relative)))
        if app == "Tensorflow":
            overhead = (1 - geomean) * 100
        else:
            overhead = (geomean - 1) * 100
        print(f"{app}: {relative}")
        print(f"Geometric mean of relative values for {app}: {geomean}")
        print(f"Overhead for {app}: {overhead:.2f}%")

        if rel:
            # plot rel using right axis
            if i == 2:
                # don't plot relative value for small
                relative[0] = np.nan
            ax2 = ax[i].twinx()
            ax2.plot(
                labels,
                relative,
                color="gray",
                marker="o",
                markersize=1,
                label="Relative",
            )
            if i == 2:
                ax2.set_ylabel("Relative Performance", color="black", fontsize=5)
                ax2.tick_params(axis="y", labelcolor="black")
            else:
                # remove ylabel
                ax2.set_ylabel("")

            # ax2.set_ylim([0, 1.5])
            ax2.set_ylim([0.8, 1.2])
            # draw 1.0 line
            ax2.axhline(y=1.0, color="black", linestyle="--", linewidth=0.5)

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

    # rotate xticklabels
    # rotation = 0
    # ax[0].set_xticklabels(labels, fontsize=6, rotation=rotation, ha="right")
    # ax[1].set_xticklabels(labels, fontsize=6, rotation=rotation, ha="right")
    # ax[2].set_xticklabels(labels, fontsize=6, rotation=rotation, ha="right")

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
                    txt = f"{bar.get_height():.1f}"
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

    sns.despine(top=True)
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if not rel:
        save_path = outdir / f"{outname}_norel{pvm}.pdf"
    else:
        save_path = outdir / f"{outname}{pvm}.pdf"
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
    result_dir=None,
):
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    vm_df = parse_sqlite_result(f"{vm}-direct-{size}-{device}-{aio}", label=vm_label)
    swiotlb_df = parse_sqlite_result(
        f"{vm}-direct-{size}{device}-{aio}-swiotlb", label="swiotlb"
    )
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
        palette=palette2,
        edgecolor="black",
        err_kws={"linewidth": 1},
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
    for patch in ax.get_legend().get_patches()[2:]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f")

    sns.despine(top=True)
    plt.tight_layout()

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / f"{outname}_{device}.pdf"
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_tensorflow_db(ctx, metric: Optional[str] = None):
    df = query_db("SELECT * FROM tensorflow")

    def determine_size(row):
        if "small" in row["name"]:
            return "small"
        elif "medium" in row["name"]:
            return "medium"
        elif "large" in row["name"]:
            return "large"
        else:
            return "xlarge"

    df["size"] = df.apply(determine_size, axis=1)
    df["name"] = df.apply(
        lambda row: row["name"]
        .replace("-direct", "")
        .replace("-medium", "")
        .replace("-large", "")
        .replace("-numa", ""),
        axis=1,
    )

    fig, ax = plt.subplots()
    sns.barplot(
        data=df,
        x="size",
        y="examples_per_sec",
        ax=ax,
        hue="name",
        palette=palette3,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput (examples/s)")
    ax.set_title("Higher is better ↑", fontsize=12, color="navy")

    if metric:
        ax2 = ax.twinx()
        METRIC_FUNCS[metric](sns, ax2, "size", "name", df, palette3)

    plt.tight_layout()
    plt.savefig(
        f"plot/tensorflow/tensorflow" + (f"_{metric}" if metric else "") + ".pdf",
        bbox_inches="tight",
    )
