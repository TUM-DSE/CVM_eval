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
hatches = ["", "//", "\\"]
hatches2 = ["", "////", "\\\\"]


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
        if "Linux: init_start" in line:
            kernel_end = float(line.split(":")[0])
            continue
        if "Linux: systemd init end" in line:
            init_end = float(line.split(":")[0])
            continue
    assert vm_start > qemu_start
    assert ovmf_end > vm_start
    assert kernel_end > ovmf_end
    assert init_end > kernel_end

    times.append(vm_start - qemu_start)
    times.append(ovmf_end - vm_start)
    times.append(kernel_end - ovmf_end)
    times.append(init_end - kernel_end)

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

    path = BENCH_RESULT_DIR / name / date

    # directory contains results of multiple runs
    results = []
    for file in os.listdir(path):
        if file.endswith(".txt"):
            with open(path / file) as f:
                result = f.readlines()
            parsed = parse_result(result)
            results.append(parsed)

    # choose median value of the total time as a result
    total_times = np.sum(results, axis=1)
    median_index = np.argsort(total_times)[len(total_times) // 2]
    return results[median_index]


def create_df(vm, cvm, index) -> pd.DataFrame:
    columns = ["QEMU", "OVMF", "Linux", "Init"]

    vm_qemu = [vm[index[i]][0] for i in range(len(index))]
    vm_ovmf = [vm[index[i]][1] for i in range(len(index))]
    vm_linux = [vm[index[i]][2] for i in range(len(index))]
    vm_init = [vm[index[i]][3] for i in range(len(index))]
    cvm_qemu = [cvm[index[i]][0] for i in range(len(index))]
    cvm_ovmf = [cvm[index[i]][1] for i in range(len(index))]
    cvm_linux = [cvm[index[i]][2] for i in range(len(index))]
    cvm_init = [cvm[index[i]][3] for i in range(len(index))]

    df1 = pd.DataFrame(
        np.array([vm_qemu, vm_ovmf, vm_linux, vm_init]).T, index=index, columns=columns
    )
    df2 = pd.DataFrame(
        np.array([cvm_qemu, cvm_ovmf, cvm_linux, cvm_init]).T,
        index=index,
        columns=columns,
    )

    data = [df1, df2]

    return data


def create_df2(vm, cvm, prealloc, index) -> pd.DataFrame:
    columns = ["QEMU", "OVMF", "Linux", "Init"]

    vm_qemu = [vm[index[i]][0] for i in range(len(index))]
    vm_ovmf = [vm[index[i]][1] for i in range(len(index))]
    vm_linux = [vm[index[i]][2] for i in range(len(index))]
    vm_init = [vm[index[i]][3] for i in range(len(index))]
    cvm_qemu = [cvm[index[i]][0] for i in range(len(index))]
    cvm_ovmf = [cvm[index[i]][1] for i in range(len(index))]
    cvm_linux = [cvm[index[i]][2] for i in range(len(index))]
    cvm_init = [cvm[index[i]][3] for i in range(len(index))]
    prealloc_qemu = [prealloc[index[i]][0] for i in range(len(index))]
    prealloc_ovmf = [prealloc[index[i]][1] for i in range(len(index))]
    prealloc_linux = [prealloc[index[i]][2] for i in range(len(index))]
    prealloc_init = [prealloc[index[i]][3] for i in range(len(index))]

    df1 = pd.DataFrame(
        np.array([vm_qemu, vm_ovmf, vm_linux, vm_init]).T, index=index, columns=columns
    )
    df2 = pd.DataFrame(
        np.array([cvm_qemu, cvm_ovmf, cvm_linux, cvm_init]).T,
        index=index,
        columns=columns,
    )
    df3 = pd.DataFrame(
        np.array([prealloc_qemu, prealloc_ovmf, prealloc_linux, prealloc_init]).T,
        index=index,
        columns=columns,
    )

    data = [df1, df2, df3]

    return data


# https://stackoverflow.com/questions/22787209/how-to-have-clusters-of-stacked-bars
def plot_clustered_stacked(
    dfall, labels=None, title="multiple stacked bar plot", H="/", cvm="snp", **kwargs
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
            axe.bar_label(container, fmt="%.2f", fontsize=4, label_type="center")

    h, l = axe.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i : i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(hatches[i % len(hatches)])  # edited part
                #rect.set_hatch(H * int(i / n_col))  # edited part
                rect.set_width(1 / float(n_df + 1))

    axe.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2.0)
    axe.set_xticklabels(df.index, rotation=0, fontsize=FONTSIZE)

    # Add invisible data to add another legend
    n = []
    for i in range(n_df):
        #n.append(axe.bar(0, 0, color="white", edgecolor="k", hatch=H * i * 2))
        n.append(axe.bar(0, 0, color="white", edgecolor="k", hatch=hatches2[i % len(hatches2)]))

    # l1 = axe.legend(h[:n_col], l[:n_col], loc=[1.01, 0.5])
    l1 = axe.legend(
        h[:n_col],
        l[:n_col],
        ncol=4,
        # bbox_to_anchor=[0.60, -0.20],
        # bbox_to_anchor=[0.60, 0.00],
        labelspacing=0.2,
        columnspacing=0.5,
        handletextpad=0.2,
        fontsize=5,
        loc="upper left",
    )
    if labels is not None:
        # l2 = plt.legend(n, labels, loc=[1.01, 0.1])
        l2 = plt.legend(
            n,
            labels,
            ncol=3,
            labelspacing=0.2,
            columnspacing=0.5,
            handletextpad=0.2,
            fontsize=5,
            # bbox_to_anchor=[1.0, -0.15],
            bbox_to_anchor=[0, 0.90],
            loc="upper left",
        )
    axe.add_artist(l1)

    # calculate the total time
    for i in range(n_df):
        total_time = (
            dfall[i]["QEMU"] + dfall[i]["OVMF"] + dfall[i]["Linux"] + dfall[i]["Init"]
        ).values
        # put the total time on the top of the bar
        for j in range(len(total_time)):
            p = axe.patches[j + i * len(total_time)]
            space = 0.3
            if cvm == "snp":
                space = 0.2
            axe.text(
                p.get_x() + (space) * i + p.get_width() / 2.0,
                total_time[j] + 0.1,
                f"{total_time[j]:.2f}",
                ha="center",
                va="bottom",
                fontsize=5,
            )
    # vm_total_time = (dfall[0]["QEMU"] + dfall[0]["OVMF"] + dfall[0]["Linux"] + dfall[0]["Init"]).values
    # cvm_total_time = (dfall[1]["QEMU"] + dfall[1]["OVMF"] + dfall[1]["Linux"] + dfall[1]["Init"]).values
    ## put the total time on the top of the bar
    # for i in range(len(vm_total_time)):
    #    p = axe.patches[i]
    #    axe.text(
    #        p.get_x() + p.get_width() / 2.0,
    #        vm_total_time[i] + 0.1,
    #        f"{vm_total_time[i]:.2f}",
    #        ha="center",
    #        va="bottom",
    #        fontsize=5,
    #    )
    # for i in range(len(cvm_total_time)):
    #    p = axe.patches[i + len(vm_total_time)]
    #    axe.text(
    #        p.get_x() + 0.3 + p.get_width() / 2.0,
    #        cvm_total_time[i] + 0.1,
    #        f"{cvm_total_time[i]:.2f}",
    #        ha="center",
    #        va="bottom",
    #        fontsize=5,
    #    )

    return axe


@task
def plot_boottime(
    ctx: Any,
    cvm: str = "snp",
    prealloc: bool = True,
    outdir: str = "plot",
    sizes: list = [],
    labels: list = [],
    result_dir=None,
) -> None:
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
        memsize = [8, 64, 256, 512]
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        memsize = [8, 64, 128, 256]

    # to change sizes, use `--sizes` option multiple times. e.g.,
    # % inv boottime.plot-boottime --sizes small --sizes medium --sizes large
    if len(sizes) == 0:
        sizes = ["small", "medium", "large", "numa"]
        labels = ["small", "medium", "large", "xlarge"]
    print(sizes)
    vm_ = {}
    cvm_ = {}
    p = ""
    if not prealloc:
        p = "-no-prealloc"
    for size, label in zip(sizes, labels):
        vm_[label] = load_data(f"{vm}-direct-{size}")
        cvm_[label] = load_data(f"{cvm}-direct-{size}{p}")
    df = create_df(vm_, cvm_, labels)
    print(df)

    ax = plot_clustered_stacked(df, [vm_label, cvm_label],cvm=cvm, color=palette)

    ax.set_ylabel("Time (s)")
    ax.set_xlabel("")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")

    # plot memory size
    # ax2 = ax.twinx()
    # ax2.plot(memsize)
    # ax2.set_ylabel("Memory size (GB)")
    # ax2.set_yticks(np.arange(0, 2 * len(memsize), 2))
    # ax2.set_yticklabels(memsize)
    # ax2.set_ylim(ax.get_ylim())
    # ax2.yaxis.set_ticks_position("right")
    # ax2.yaxis.set_label_position("right")

    # sns.despine()
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        outdir / f"boottime{p}.pdf", format="pdf", pad_inches=0, bbox_inches="tight"
    )
    print(f"Output written to {outdir}/boottime{p}.pdf")


@task
def plot_boottime2(
    ctx: Any,
    cvm: str = "snp",
    cpu: bool = False,
    prealloc: bool = True,
    outdir: str = "plot",
    result_dir=None,
) -> None:
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
        memsize = [8, 16, 32, 64, 128, 256]
        # cpusize = [1, 8, 16, 28, 32, 56, 64]
        cpusize = [1, 8, 16, 28, 56]
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        memsize = [8, 16, 32, 64, 128, 256]
        cpusize = [1, 8, 16, 28, 56]

    vm_ = {}
    cvm_ = {}
    p = ""
    if not prealloc:
        p = "-no-prealloc"
    if cpu:
        for cpu in cpusize:
            vm_[cpu] = load_data(f"{vm}-direct-boot-cpu{cpu}")
            cvm_[cpu] = load_data(f"{cvm}-direct-boot-cpu{cpu}{p}")
        df = create_df(vm_, cvm_, cpusize)
    else:
        for mem in memsize:
            vm_[mem] = load_data(f"{vm}-direct-boot-mem{mem}")
            cvm_[mem] = load_data(f"{cvm}-direct-boot-mem{mem}{p}")
        df = create_df(vm_, cvm_, memsize)
    print(df)

    ax = plot_clustered_stacked(df, [vm_label, cvm_label], cvm=cvm, color=palette)

    ax.set_ylabel("Time (s)")
    if cpu:
        ax.set_xlabel("Number of vCPUs")
    else:
        ax.set_xlabel("Memory size (GB)")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    sns.despine(top = True)
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if cpu:
        outname = f"boottime{p}_cpu.pdf"
    else:
        outname = f"boottime{p}_memory.pdf"

    plt.savefig(outdir / outname, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"Output written to {outdir}/{outname}")


@task
def plot_boottime3(
    ctx: Any,
    cvm: str = "snp",
    cpu: bool = False,
    outdir: str = "plot",
    result_dir=None,
) -> None:
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
        memsize = [8, 16, 32, 64, 128, 256]
        cpusize = [1, 8, 16, 28, 56]
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        memsize = [8, 16, 32, 64, 128, 256]
        cpusize = [1, 8, 16, 28, 56]

    vm_ = {}
    cvm_ = {}
    prealloc_ = {}

    if cpu:
        for cpu in cpusize:
            vm_[cpu] = load_data(f"{vm}-direct-boot-cpu{cpu}")
            cvm_[cpu] = load_data(f"{cvm}-direct-boot-cpu{cpu}-no-prealloc")
            prealloc_[cpu] = load_data(f"{cvm}-direct-boot-cpu{cpu}")
        df = create_df2(vm_, cvm_, prealloc_, cpusize)
    else:
        for mem in memsize:
            vm_[mem] = load_data(f"{vm}-direct-boot-mem{mem}")
            cvm_[mem] = load_data(f"{cvm}-direct-boot-mem{mem}-no-prealloc")
            prealloc_[mem] = load_data(f"{cvm}-direct-boot-mem{mem}")
        df = create_df2(vm_, cvm_, prealloc_, memsize)
    print(df)

    ax = plot_clustered_stacked(df, [vm_label, cvm_label, "preallcoc"], cvm=cvm, color=palette)

    ax.set_ylabel("Time (s)")
    if cpu:
        ax.set_xlabel("Number of vCPUs")
    else:
        ax.set_xlabel("Memory size (GB)")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if cpu:
        outname = f"boottime_all_cpu.pdf"
    else:
        outname = f"boottime_all_memory.pdf"

    plt.savefig(outdir / outname, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"Output written to {outdir}/{outname}")


@task
def plot_boottime_snp(
    ctx: Any,
    cvm: str = "snp",
    cpu: bool = False,
    version: str = "6.9",
    outdir: str = "plot",
    result_dir=None,
) -> None:
    global BENCH_RESULT_DIR
    if result_dir is not None:
        BENCH_RESULT_DIR = Path(result_dir)
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
        memsize = [8, 16, 32, 64, 128, 256]
        cpusize = [1, 8, 16, 28, 56]
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"
        memsize = [8, 16, 32, 64, 128, 256]
        cpusize = [1, 8, 16, 28, 56]

    vm_ = {}
    cvm_ = {}
    cvm2_ = {}

    if cpu:
        for cpu in cpusize:
            vm_[cpu] = load_data(f"{vm}-direct-boot-cpu{cpu}")
            cvm_[cpu] = load_data(f"{cvm}-direct-boot-cpu{cpu}-no-prealloc")
            bench_result_dir_old = BENCH_RESULT_DIR
            BENCH_RESULT_DIR = BENCH_RESULT_DIR / ".." / f"v{version}" / "boottime"
            cvm2_[cpu] = load_data(f"{cvm}-direct-boot-cpu{cpu}-no-prealloc")
            BENCH_RESULT_DIR = bench_result_dir_old
        df = create_df2(vm_, cvm_, cvm2_, cpusize)
    else:
        for mem in memsize:
            vm_[mem] = load_data(f"{vm}-direct-boot-mem{mem}")
            cvm_[mem] = load_data(f"{cvm}-direct-boot-mem{mem}-no-prealloc")
            bench_result_dir_old = BENCH_RESULT_DIR
            BENCH_RESULT_DIR = BENCH_RESULT_DIR / ".." / f"v{version}" / "boottime"
            cvm2_[mem] = load_data(f"{cvm}-direct-boot-mem{mem}-no-prealloc")
            BENCH_RESULT_DIR = bench_result_dir_old
        df = create_df2(vm_, cvm_, cvm2_, memsize)
    print(df)

    if "_" in version:
        version_num = version.split("_")[0]
    else:
        version_num = version
    ax = plot_clustered_stacked(
        df, [vm_label, "snp6.8", f"snp{version_num}"], color=palette, cvm=cvm
    )

    ax.set_ylabel("Time (s)")
    if cpu:
        ax.set_xlabel("Number of vCPUs")
    else:
        ax.set_xlabel("Memory size (GB)")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")
    # sns.despine()
    sns.despine(top = True)
    plt.tight_layout()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if cpu:
        outname = f"boottime_snp_cpu_{version}.pdf"
    else:
        outname = f"boottime_snp_memory_{version}.pdf"

    plt.savefig(outdir / outname, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"Output written to {outdir}/{outname}")
