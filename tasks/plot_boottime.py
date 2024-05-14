#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Union
from pathlib import Path
import os

from invoke import task
import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
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
hatches = ["", "//"]


# return a list of elapsed time of (1) VM start, (2) Linux start (OVMF end),
# and (3) Linux user space start
def parse_result(result: list) -> List[float]:
    """Example of file
    Attaching 12 probes...
    1426251474064858: QEMU: main
    1426251488196857: QEMU: kvm_arch_init
    1426251488206197: QEMU: sev_kvm_init
    1426251488209467: QEMU: sev_kvm_init done
    1426251492028713: QEMU: kvm_arch_init done
    1426251546109012: QEMU: memory_region_init_rom_device
    1426251546414504: QEMU: memory_region_init_rom_device done
    1426251613573825: QEMU: kvm_cpu_exec
    1426251835943832: 0 OVMF: PEI main start
    1426251989523477: 0 OVMF: PEI main start
    1426251989713369: 0 OVMF: PEI main start
    1426252026008653: 1 OVMF: PEI main end
    1426252031507681: 100 OVMF: DXE main end
    1426252238096758: 101 OVMF: DXE main start
    1426252757492255: 102 OVMF: EXITBOOTSERVICE
    1426252757689956: 230 Linux: kernel_start
    1426254481421586: 231 Linux: init_start
    1426255507056687: 240 Linux: systemd init end
    1426262084153397: QEMU: exit
    """

    times = []
    for line in result:
        if "QEMU: main" in line:
            qemu_start = int(line.split(":")[0])
            continue
        if "QEMU: kvm_cpu_exec" in line:
            vm_start = float(line.split(":")[0])
            continue
        if "OVMF: EXITBOOTSERVICE" in line:
            ovmf_end = float(line.split(":")[0])
            continue
        if "Linux: systemd init end" in line:
            linux_end = float(line.split(":")[0])
            continue
    assert vm_start > qemu_start
    assert ovmf_end > vm_start
    assert linux_end > ovmf_end

    times.append(vm_start - qemu_start)
    times.append(ovmf_end - vm_start)
    times.append(linux_end - ovmf_end)

    times = np.array(times)
    times /= 1e9  # convert to seconds

    return times


# bench mark path:
# ./bench-result/boottime/{name}/{date}
BENCH_RESULT_DIR = Path("./bench-result/boottime")


def load_data(name: str, date=None) -> List[float]:
    if date is None:
        # use the latest date
        date = sorted(os.listdir(BENCH_RESULT_DIR / name))[-1]

    # FIXME: how shold we plot multiple measurements?
    file = BENCH_RESULT_DIR / name / date / "1.txt"
    with open(file) as f:
        result = f.readlines()
    parsed = parse_result(result)
    return parsed


def create_df(vm, cvm, index=["small", "medium", "large"]) -> pd.DataFrame:
    columns = ["QEMU", "OVMF", "Linux"]

    vm_qemu = [vm["small"][0], vm["medium"][0], vm["large"][0]]
    vm_ovmf = [vm["small"][1], vm["medium"][1], vm["large"][1]]
    vm_linux = [vm["small"][2], vm["medium"][2], vm["large"][2]]
    cvm_qemu = [cvm["small"][0], cvm["medium"][0], cvm["large"][0]]
    cvm_ovmf = [cvm["small"][1], cvm["medium"][1], cvm["large"][1]]
    cvm_linux = [cvm["small"][2], cvm["medium"][2], cvm["large"][2]]

    df1 = pd.DataFrame(
        np.array([vm_qemu, vm_ovmf, vm_linux]).T, index=index, columns=columns
    )
    df2 = pd.DataFrame(
        np.array([cvm_qemu, cvm_ovmf, cvm_linux]).T, index=index, columns=columns
    )

    data = [df1, df2]

    return data


# https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars
def plot_clustered_stacked(
    dfall, labels=None, title="multiple stacked bar plot", H="/", **kwargs
):
    """Given a list of dataframes, with identical columns and index, create a clustered stacked bar plot.
    labels is a list of the names of the dataframe, used for the legend
    title is a string for the title of the plot
    H is the hatch used for identification of the different dataframe"""

    n_df = len(dfall)
    n_col = len(dfall[0].columns)
    n_ind = len(dfall[0].index)
    # axe = plt.subplot(111)
    fig, axe = plt.subplots(figsize=(figwidth_half, 2.2))

    for i, df in enumerate(dfall):  # for each data frame
        axe = df.plot(
            kind="bar",
            edgecolor="black",
            stacked=True,
            ax=axe,
            legend=False,
            grid=False,
            **kwargs,
        )  # make bar plots
        for container in axe.containers:
            axe.bar_label(container, fmt="%.2f", fontsize=5, label_type="center")

    h, l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i : i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.0)
    axe.set_xticklabels(df.index, rotation=0, fontsize=FONTSIZE)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="white", edgecolor="k", hatch=H * i * 2))

    # l1 = axe.legend(h[:n_col], l[:n_col], loc=[1.01, 0.5])
    l1 = axe.legend(
        h[:n_col],
        l[:n_col],
        ncol=3,
        bbox_to_anchor=[0.45, -0.20],
        labelspacing=0.2,
        columnspacing=0.5,
        handletextpad=0.2,
        fontsize=7,
    )
    if labels is not None:
        # l2 = plt.legend(n, labels, loc=[1.01, 0.1])
        l2 = plt.legend(
            n,
            labels,
            ncol=2,
            bbox_to_anchor=[1.0, -0.20],
            labelspacing=0.2,
            columnspacing=0.5,
            handletextpad=0.2,
            fontsize=7,
        )
    axe.add_artist(l1)
    return axe


@task
def plot_boottime(ctx: Any, vm="normal", cvm="snp", outdir="plot") -> None:
    sizes = ["small", "medium", "large"]
    vm_ = {}
    cvm_ = {}
    for size in sizes:
        vm_[size] = load_data(f"{vm}-direct-{size}")
        cvm_[size] = load_data(f"{cvm}-direct-{size}")
    df = create_df(vm_, cvm_)
    print(df)
    if vm == "normal":
        vm = "amd"

    ax = plot_clustered_stacked(df, [vm, cvm], color=palette)

    ax.set_ylabel("Time (s)")
    ax.set_xlabel("")

    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        outdir / "boottime.pdf", format="pdf", pad_inches=0, bbox_inches="tight"
    )
    print(f"Output written to {outdir}/boottime.pdf")
