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

# mpl.use("Agg")
# mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
# mpl.rcParams["pdf.fonttype"] = 42
# mpl.rcParams["ps.fonttype"] = 42
# mpl.rcParams["font.family"] = "libertine"
#
# sns.set_style("whitegrid")
# sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
# sns.set_context("paper", rc={"font.size": 5, "axes.titlesize": 5, "axes.labelsize": 8})
#
## 3.3 inch for single column, 7 inch for double column
# figwidth_half = 3.3
# figwidth_full = 7

FONTSIZE = 9

from motivation_plotting_config import *

pastel = sns.color_palette("pastel")
# palette = sns.color_palette("pastel")
vm_col = pastel[0]
swiotlb_col = pastel[1]
vhost_col = pastel[4]
vshot_swiotlb_col = pastel[5]
cvm_col = pastel[2]
cvm_vhost_col = pastel[3]
palette = [vm_col, swiotlb_col, vhost_col, vshot_swiotlb_col, cvm_col, cvm_vhost_col]
# hatches = ["", "//"]
hatches = ["", "", "", "", "//", "//", "//", "//", "//", "//"]

palette2 = [vm_col, vhost_col, cvm_col, cvm_vhost_col]
hatches2 = ["", "", "//", "//"]

BENCH_RESULT_DIR = Path("./bench-result/network")


def parse_iperf_result_sub(
    name: str, mode: str, date: str, lebel: str, pkt_size: [int]
) -> pd.DataFrame:
    ths = []
    for size in pkt_size:
        file = BENCH_RESULT_DIR / "iperf" / name / mode / date / f"{size}.log"
        with file.open("r") as f:
            lines = f.readlines()

        # example format:
        # > [SUM]   0.00-10.00  sec  11.7 GBytes  10.1 Gbits/sec                  receiver
        # find the line with [SUM] from the end
        for line in reversed(lines):
            if "[SUM]" in line:
                break
        else:
            raise ValueError("No [SUM] line found")
        th = float(line.split()[5])
        if line.split()[6] == "Mbits/sec":
            th /= 1000.0
        ths.append(th)

    df = pd.DataFrame({"name": lebel, "size": pkt_size, "throughput": ths})
    return df


# bench mark path:
# ./bench-result/network/iperf/{name}/{date}
def parse_iperf_result(
    name: str, label: str, mode: str, date=None, pkt=None, max_num: int = 10
) -> pd.DataFrame:
    # create df like the following
    # | VM | pkt size | throughput |
    # |----|----------|------------|
    # |    |          |            |
    if pkt is not None:
        pktsize = [pkt]
    elif mode == "udp":
        pktsize = [64, 128, 256, 512, 1024, 1460]
    elif mode == "tcp":
        pktsize = [64, 128, 256, 512, 1024, "32K", "128K"]
    else:
        raise ValueError(f"Invalid mode: {mode}")

    dates = []
    if date is None:
        # use the latest date
        dates = sorted(os.listdir(BENCH_RESULT_DIR / "iperf" / name / mode))[-max_num:]
    else:
        dates.append(date)

    dfs = []
    for date in dates:
        df = parse_iperf_result_sub(name, mode, date, label, pktsize)
        dfs.append(df)

    df = pd.concat(dfs)

    return df


def parse_ping_result(name: str, label: str, date=None, all=False) -> pd.DataFrame:
    if all:
        pktsize = [64, 128, 256, 512, 1024, 1460]
        pktsize_actual = [64, 128, 256, 512, 1024, 1460]
    else:
        pktsize = [64]
        pktsize_actual = [64]
    pktsize_ = []
    lats = []

    if date is None:
        # use the latest date
        date = sorted(os.listdir(BENCH_RESULT_DIR / "ping" / name))[-1]

    print(f"date: {date}")

    for size in pktsize_actual:
        path = Path(f"./bench-result/network/ping/{name}/{date}/{size}.log")
        if not path.exists():
            print(f"XXX: {path} not found!")
            continue
        with path.open("r") as f:
            lines = f.readlines()

        # example format:
        # > 128 bytes from 172.44.0.2: icmp_seq=1 ttl=64 time=0.131 ms
        # > 128 bytes from 172.44.0.2: icmp_seq=2 ttl=64 time=0.221 ms
        # > 128 bytes from 172.44.0.2: icmp_seq=3 ttl=64 time=0.212 ms
        # > 128 bytes from 172.44.0.2: icmp_seq=4 ttl=64 time=0.200 ms
        lats_ = []
        for line in lines:
            if "icmp_seq" in line:
                lats_.append(float(line.split()[6].split("=")[1]))
        # drop firt 3 pings to get stable result
        lats_ = lats_[3:]
        lats.extend(lats_)
        pktsize_.extend([size] * len(lats_))

    df = pd.DataFrame({"name": label, "size": pktsize_, "latency": lats})
    return df


def parse_memtier_result_sub(
    path: str, label: str, server: str, tls: bool = False
) -> pd.DataFrame:
    """
        Example output:
        ```
    Type         Ops/sec     Hits/sec   Misses/sec    Avg. Latency     p50 Latency     p99 Latency   p99.9 Latency       KB/sec
    ----------------------------------------------------------------------------------------------------------------------------
    Sets        47686.59          ---          ---        62.87207        37.37500       716.79900       937.98300      3672.70
    Gets       476341.91         0.00    476341.91        62.40503        37.37500       716.79900       937.98300     18090.40
    Waits           0.00          ---          ---             ---             ---             ---             ---          ---
    Totals     524028.51         0.00    476341.91        62.44752        37.37500       716.79900       937.98300     21763.10
    ```
    """
    print(path)
    if tls:
        tls_ = " (tls)"
    else:
        tls_ = ""
    workloads = []
    ths = []
    with open(path, "r") as f:
        lines = f.readlines()

        for line in lines:
            if line.startswith("Gets"):
                th = float(line.split()[1].strip()) / 1e6
                ths.append(th)
                workloads.append(f"GET{tls_}")
            elif line.startswith("Sets"):
                th = float(line.split()[1].strip()) / 1e6
                ths.append(th)
                workloads.append(f"SET{tls_}")

    df = pd.DataFrame(
        {"name": label, "workload": workloads, "throughput": ths, "server": server}
    )
    return df


def parse_memtier_result(
    name: str, label: str, server: str, date=None, date_tls=None, max_num: int = 10
) -> pd.DataFrame:
    dates = []

    if date is None:
        dates = sorted(os.listdir(BENCH_RESULT_DIR / "memtier" / server / name))[
            -max_num:
        ]
    else:
        dates.append(date)

    dfs = []
    for date in dates:
        df = parse_memtier_result_sub(
            BENCH_RESULT_DIR / "memtier" / server / name / date / "memtier.log",
            label,
            server,
            False,
        )
        if date_tls is None:
            date_tls = sorted(
                os.listdir(BENCH_RESULT_DIR / "memtier" / f"{server}-tls" / name)
            )[-1]
        df_tls = parse_memtier_result_sub(
            BENCH_RESULT_DIR
            / "memtier"
            / f"{server}-tls"
            / name
            / date_tls
            / "memtier.log",
            f"{label}",
            server,
            True,
        )
        dfs.append(df)
        dfs.append(df_tls)

    df = pd.concat(dfs)

    return df


def parse_nginx_result_sub(path: str, name: str, workload: str) -> pd.DataFrame:
    """
        Example output:
    ```
    Running 10s test @ http://172.44.0.2
      2 threads and 10 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency    21.41ms    2.07ms  89.21ms   91.82%
        Req/Sec   234.56     16.83   350.00     83.00%
      4674 requests in 10.01s, 1.16MB read
    Requests/sec:    467.10
    Transfer/sec:    118.60KB
    ```
    """
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "Requests/sec" in line:
                th = float(line.split()[1])
                break
    df = pd.DataFrame({"name": [name], "workload": [workload], "throughput": [th]})
    return df


def parse_nginx_result(
    name: str, label: str, date=None, max_num: int = 10
) -> pd.DataFrame:
    dates = []
    if date is None:
        dates = sorted(os.listdir(BENCH_RESULT_DIR / "nginx" / name))[-max_num:]
    else:
        dates.append(date)

    dfs = []
    for date in dates:
        df = parse_nginx_result_sub(
            BENCH_RESULT_DIR / "nginx" / name / date / "http.log", label, "http"
        )
        df_ssl = parse_nginx_result_sub(
            BENCH_RESULT_DIR / "nginx" / name / date / "https.log", label, "https"
        )

        dfs.append(df)
        dfs.append(df_ssl)

    df = pd.concat(dfs)

    return df


@task
def plot_iperf(
    ctx,
    cvm="snp",
    mode="udp",
    vhost=False,
    mq=False,
    tmebypass=False,
    poll=False,
    plot_all=False,
    plot_hpoll=False,
    outdir="plot",
    outname=None,
    size="medium",
    pkt=None,
    vhost_only=False,
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

    def get_name(name, p, vhost=False, mq=mq, swiotlb=False):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        if swiotlb:
            n += "-swiotlb"
        return n

    dfs = []

    if vhost_only:
        dfs.append(
            parse_iperf_result(get_name(vm, pvm, vhost=True), f"VM", mode, pkt=pkt)
        )
        dfs.append(
            parse_iperf_result(
                get_name(vm, pvm, vhost=True, swiotlb=True), f"VM (+BB)", mode, pkt=pkt
            )
        )
        dfs.append(
            parse_iperf_result(
                get_name(cvm, pcvm, vhost=True), f"CVM (+BB+Enc)", mode, pkt=pkt
            )
        )
        if plot_hpoll:
            dfs.append(
                parse_iperf_result(
                    get_name(cvm, "-haltpoll-vhost"),
                    f"CVM (+BB+Enc+HPoll)",
                    mode,
                    pkt=pkt,
                )
            )
    else:
        dfs.append(parse_iperf_result(get_name(vm, pvm), vm_label, mode, pkt=pkt))
        dfs.append(
            parse_iperf_result(
                get_name(vm, pvm, vhost=False, swiotlb=True), f"swiotlb", mode, pkt=pkt
            )
        )
        dfs.append(
            parse_iperf_result(get_name(vm, pvm, vhost=True), f"vhost", mode, pkt=pkt)
        )
        dfs.append(
            parse_iperf_result(
                get_name(vm, pvm, vhost=True, swiotlb=True),
                f"vhost-swiotlb",
                mode,
                pkt=pkt,
            )
        )
        dfs.append(parse_iperf_result(get_name(cvm, pcvm), cvm_label, mode, pkt=pkt))
        dfs.append(
            parse_iperf_result(
                get_name(cvm, pcvm, vhost=True), f"{cvm_label}-vhost", mode, pkt=pkt
            )
        )
    if plot_all:
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-haltpoll"), f"{cvm_label}-hpoll", mode, pkt=pkt
            )
        )
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-poll"), f"{cvm_label}-poll", mode, pkt=pkt
            )
        )
    if plot_all:
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-haltpoll-vhost"),
                f"{cvm_label}-vhost-hpoll",
                mode,
                pkt=pkt,
            )
        )
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-poll-vhost"), f"{cvm_label}-vhost-poll", mode, pkt=pkt
            )
        )
    if not vhost_only and plot_hpoll:
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-haltpoll"), f"{cvm_label}-hpoll", mode, pkt=pkt
            )
        )
        dfs.append(
            parse_iperf_result(
                get_name(cvm, "-haltpoll-vhost"),
                f"{cvm_label}-vhost-hpoll",
                mode,
                pkt=pkt,
            )
        )
    df = pd.concat(dfs)
    print(df)

    # plot thropughput
    # fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    fig, ax = create_standardized_plot(
        ax_height=0.95, top_margin=0.45, bottom_margin=0.46
    )

    sns.barplot(
        x="size",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
        linewidth=0.5,
        width=0.8,
        err_kws={"linewidth": 1},
    )
    if pkt is not None:
        ax.set_xticklabels([])
        # ax.set_xlabel(f"Buffer Size {pkt} byte")
        ax.set_xlabel(f"UDP iperf (pkt size 1460)", fontsize=TICKS_FONTSIZE)
        # ax.set_ylim(0, 4)
    else:
        ax.set_xlabel("Packet Size (byte)")
    ax.set_ylabel("Throughput (Gbps)", fontsize=TICKS_FONTSIZE)
    ax.set_title("Higher is better ↑", fontsize=TITLE_FONTSIZE, color="navy")
    plt.yticks(fontsize=TICKS_FONTSIZE)
    ax.yaxis.offsetText.set_fontsize(TICKS_FONTSIZE)

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = len(df["size"].unique())
    for hatch in hatches:
        hs.extend([hatch] * num_x)
    num_legend = len(bars) - len(hs)
    hs.extend([""] * num_legend)
    for bar, hatch in zip(bars, hs):
        bar.set_hatch(hatch)

    # set hatch for the legend
    # plt.legend(fontsize=LEGEND_FONTSIZE, loc='upper left',
    #           bbox_to_anchor=(0.01, 0.98))
    # handles, labels = ax.get_legend_handles_labels()
    # fig.legend(handles, labels, fontsize=LEGEND_FONTSIZE, loc='center',
    #           bbox_to_anchor=(0.5, 0.91),
    #           edgecolor='black', borderaxespad=0.,
    #           frameon=True, ncols=3, columnspacing=0.3, labelspacing=0.2,
    #           borderpad=0.3, handletextpad=0.3)
    plt.legend(
        fontsize=LEGEND_FONTSIZE,
        loc="center",
        bbox_to_anchor=(0.5, 1.40),
        # bbox_to_anchor=(0.5, 0.91),
        edgecolor="black",
        borderaxespad=0.0,
        frameon=True,
        ncols=3,
        columnspacing=0.3,
        labelspacing=0.2,
        borderpad=0.3,
        handletextpad=0.3,
    )
    for patch in ax.get_legend().get_patches()[:4]:
        patch.set_hatch("")
    for patch in ax.get_legend().get_patches()[4:]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        if mode == "udp":
            # ax.bar_label(container, fmt="%.2f", fontsize=5, rotation=90, padding=2)
            ax.bar_label(
                container, fmt="%.2f", fontsize=ANNOTATION_SIZE, rotation=0, padding=2
            )
        else:
            ax.bar_label(container, fmt="%.2f", fontsize=5)

    plt.tight_layout()

    if outname is None:
        outname = f"iperf_{mode}"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        if pkt is not None:
            outname += f"_{pkt}"
        if vhost_only:
            outname += "_vhost_only"
        outname += f"_throughput{pvm}"
    if plot_all:
        outname += "_all"
    outname += ".pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_iperf2(
    ctx,
    cvm="snp",
    mode="udp",
    vhost=False,
    mq=False,
    tmebypass=False,
    poll=False,
    plot_all=False,
    plot_hpoll=False,
    outdir="plot",
    outname=None,
    size="medium",
    pkt=None,
    vhost_only=False,
    result_dir=None,
):
    if pkt is None:
        pkt = 1024
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

    def get_name(name, p, vhost=False, mq=mq, swiotlb=False):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        if swiotlb:
            n += "-swiotlb"
        return n

    dfs = []

    dfs.append(parse_iperf_result(get_name(vm, pvm), vm_label, mode, pkt=pkt))
    dfs.append(
        parse_iperf_result(
            get_name(vm, pvm, vhost=False, swiotlb=True), f"swiotlb", mode, pkt=pkt
        )
    )
    dfs.append(
        parse_iperf_result(get_name(vm, pvm, vhost=True), f"vhost", mode, pkt=pkt)
    )
    dfs.append(
        parse_iperf_result(
            get_name(vm, pvm, vhost=True, swiotlb=True), f"vhost-swiotlb", mode, pkt=pkt
        )
    )
    dfs.append(parse_iperf_result(get_name(cvm, pcvm), cvm_label, mode, pkt=pkt))
    dfs.append(
        parse_iperf_result(
            get_name(cvm, pcvm, vhost=True), f"{cvm_label}-vhost", mode, pkt=pkt
        )
    )
    dfs.append(
        parse_iperf_result(
            get_name(cvm, "-haltpoll"), f"{cvm_label}-hpoll", mode, pkt=pkt
        )
    )
    dfs.append(
        parse_iperf_result(
            get_name(cvm, "-haltpoll-vhost"),
            f"{cvm_label}-vhost-hpoll",
            mode,
            pkt=pkt,
        )
    )
    df = pd.concat(dfs)
    print(df)

    # plot thropughput
    fig, ax = create_standardized_plot(
        ax_height=0.95, top_margin=0.45, bottom_margin=0.46
    )
    # fig, ax = create_standardized_plot(ax_height = 0.95, top_margin = 0.25, bottom_margin = 0.66)

    sns.barplot(
        x="size",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=PALETTE_PASTEL,
        edgecolor="black",
        linewidth=0.0,
        width=0.8,
        err_kws={"linewidth": 1},
    )
    ax.set_xticklabels(["Networking variants"], fontsize=AXIS_LABEL_FONTSIZE)
    ax.set_ylim(0, 4)
    apply_consistent_style(
        ax,
        # title=LOWER_BETTER_TITLE,
        title=f"(c) Network performance with iPerf ({HIGHER_BETTER_TITLE})",
        # xlabel="Network performance with iPerf",
        #xlabel="Networking variatnts",
        xlabel="",
        ylabel="Throughput (Gbps)",
        labelpad=17,
    )
    plt.yticks(fontsize=TICKS_FONTSIZE)
    ax.yaxis.offsetText.set_fontsize(TICKS_FONTSIZE)

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    for barh, hatch in zip(bars, HATCHES):
        barh.set_hatch(hatch)
    # hs = []
    # num_x = len(df["size"].unique())
    # for hatch in hatches:
    #    hs.extend([hatch] * num_x)
    # num_legend = len(bars) - len(hs)
    # hs.extend([""] * num_legend)
    # for bar, hatch in zip(bars, hs):
    #    bar.set_hatch(hatch)

    # legend
    plt.legend(
        fontsize=LEGEND_FONTSIZE,
        loc="center",
        bbox_to_anchor=(0.5, 1.30),
        edgecolor="black",
        borderaxespad=0.0,
        frameon=True,
        ncols=3,
        columnspacing=0.3,
        labelspacing=0.2,
        borderpad=0.3,
        handletextpad=0.3,
    )
    for patch, hatch in zip(ax.get_legend().get_patches(), HATCHES):
        patch.set_hatch(hatch)

    # annotate values on top of each bar
    for container in ax.containers:
        ax.bar_label(
            container, fmt="%.2f", fontsize=ANNOTATION_SIZE, rotation=0, padding=0
        )

    plt.tight_layout()

    outname = f"iperf_udp_{pkt}_throughput2.pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_ping(
    ctx,
    cvm="snp",
    vhost=False,
    mq=False,
    tmebypass=False,
    poll=False,
    outdir="plot",
    outname=None,
    size="medium",
    all=False,
    result_dir=None,
):
    if result_dir is not None:
        global BENCH_RESULT_DIR
        BENCH_RESULT_DIR = Path
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

    def get_name(name, p, vhost=False, mq=mq, swiotlb=False):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        if swiotlb:
            n += "-swiotlb"
        return n

    dfs = []
    dfs.append(parse_ping_result(get_name(vm, pvm), vm_label, all=all))
    dfs.append(
        parse_ping_result(
            get_name(vm, pvm, vhost=False, swiotlb=True), f"swiotlb", all=all
        )
    )
    dfs.append(parse_ping_result(get_name(vm, pvm, vhost=True), f"vhost", all=all))
    dfs.append(
        parse_ping_result(
            get_name(vm, pvm, vhost=True, swiotlb=True), f"vhost-swiotlb", all=all
        )
    )
    dfs.append(parse_ping_result(get_name(cvm, pcvm), cvm_label, all=all))
    # dfs.append(
    #    parse_ping_result(get_name(cvm, "-haltpoll"), f"{cvm_label}-hpoll", all=all)
    # )
    # dfs.append(parse_ping_result(get_name(cvm, "-poll"), f"{cvm_label}-poll", all=all))
    dfs.append(
        parse_ping_result(
            get_name(cvm, pcvm, vhost=True), f"{cvm_label}-vhost", all=all
        )
    )
    # dfs.append(
    #    parse_ping_result(
    #        get_name(cvm, "-haltpoll", vhost=True), f"{cvm_label}-vhost-hpoll", all=all
    #    )
    # )
    # dfs.append(
    #    parse_ping_result(
    #        get_name(cvm, "-poll", vhost=True), f"{cvm_label}-vhost-poll", all=all
    #    )
    # )
    df = pd.concat(dfs)
    print(df)

    # plot thropughput
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="size",
        y="latency",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    if not all:
        ax.set_xticklabels([])
        ax.set_xlabel("Ping (64 byte)")
    else:
        ax.set_xlabel("Packet Size (byte)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Lower is better ↓", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = len(df["size"].unique())
    for hatch in hatches:
        hs.extend([hatch] * num_x)
    num_legend = len(bars) - len(hs)
    hs.extend([""] * num_legend)
    for bar, hatch in zip(bars, hs):
        bar.set_hatch(hatch)

    # set hatch for the legend
    print(ax.get_legend().get_patches())
    plt.legend(fontsize=5)
    for patch in ax.get_legend().get_patches()[4:]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f")

    plt.tight_layout()

    if outname is None:
        outname = f"ping"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        if all:
            outname += "_all"
        outname += f"{pvm}.pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_redis(
    ctx,
    cvm="snp",
    vhost=False,
    mq=False,
    outdir="plot",
    outname=None,
    size="medium",
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

    def get_name(name, vhost=False, p="", mq=mq):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_memtier_result(get_name(vm), vm_label, "redis"))
    dfs.append(parse_memtier_result(get_name(vm, vhost=True), f"vhost", "redis"))
    dfs.append(parse_memtier_result(get_name(cvm), cvm_label, "redis"))
    dfs.append(
        parse_memtier_result(
            get_name(cvm, p="-haltpoll"), f"{cvm_label}-hpoll", "redis"
        )
    )
    dfs.append(
        parse_memtier_result(get_name(cvm, p="-poll"), f"{cvm_label}-poll", "redis")
    )
    dfs.append(
        parse_memtier_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost", "redis")
    )
    dfs.append(
        parse_memtier_result(
            get_name(cvm, vhost=True, p="-haltpoll"),
            f"{cvm_label}-hpoll-vhost",
            "redis",
        )
    )
    dfs.append(
        parse_memtier_result(
            get_name(cvm, vhost=True, p="-poll"), f"{cvm_label}-poll-vhost", "redis"
        )
    )
    df = pd.concat(dfs)
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette2,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set legend ncol
    ax.legend(loc="center", ncol=2, fontsize=5)

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
        ax.bar_label(container, fmt="%.2f")

    plt.tight_layout()

    if outname is None:
        outname = f"redis"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        outname += ".pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_memcached(
    ctx,
    cvm="snp",
    vhost=False,
    mq=False,
    outdir="plot",
    outname=None,
    size="medium",
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

    def get_name(name, vhost=False, p="", mq=mq):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_memtier_result(get_name(vm), vm_label, "memcached"))
    dfs.append(parse_memtier_result(get_name(vm, vhost=True), f"vhost", "memcached"))
    dfs.append(parse_memtier_result(get_name(cvm), cvm_label, "memcached"))
    dfs.append(
        parse_memtier_result(
            get_name(cvm, p="-haltpoll"), f"{cvm_label}-hpoll", "memcached"
        )
    )
    dfs.append(
        parse_memtier_result(get_name(cvm, p="-poll"), f"{cvm_label}-poll", "memcached")
    )
    dfs.append(
        parse_memtier_result(
            get_name(cvm, vhost=True), f"{cvm_label}-vhost", "memcached"
        )
    )
    dfs.append(
        parse_memtier_result(
            get_name(cvm, vhost=True, p="-haltpoll"),
            f"{cvm_label}-hpoll-vhost",
            "memcached",
        )
    )
    dfs.append(
        parse_memtier_result(
            get_name(cvm, vhost=True, p="-poll"), f"{cvm_label}-poll-vhost", "memcached"
        )
    )
    df = pd.concat(dfs)
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette2,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set legend ncol
    ax.legend(loc="center", ncol=2, fontsize=5)

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
    # for patch in ax.get_legend().get_patches()[1::2]:
    for patch in ax.get_legend().get_patches()[2:]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f")

    plt.tight_layout()

    if outname is None:
        outname = f"memcached"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        outname += ".pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_nginx(
    ctx,
    cvm="snp",
    vhost=False,
    mq=False,
    outdir="plot",
    outname=None,
    size="medium",
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

    def get_name(name, vhost=False, p="", mq=mq):
        n = f"{name}-direct-{size}{p}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_nginx_result(get_name(vm), vm_label))
    dfs.append(parse_nginx_result(get_name(vm, vhost=True), f"vhost"))
    dfs.append(parse_nginx_result(get_name(cvm), cvm_label))
    dfs.append(parse_nginx_result(get_name(cvm, p="-haltpoll"), f"{cvm_label}-hpoll"))
    dfs.append(parse_nginx_result(get_name(cvm, p="-poll"), f"{cvm_label}-poll"))
    dfs.append(parse_nginx_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost"))
    dfs.append(
        parse_nginx_result(
            get_name(cvm, vhost=True, p="-haltpoll"), f"{cvm_label}-vhost-hpoll"
        )
    )
    dfs.append(
        parse_nginx_result(
            get_name(cvm, vhost=True, p="-poll"), f"{cvm_label}-vhost-poll"
        )
    )
    ## merge df using name as key
    df = pd.concat(dfs)
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette2,
        edgecolor="black",
        err_kws={"linewidth": 1},
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set legend ncol
    ax.legend(loc="lower center", ncol=2, fontsize=5)

    # set hatch
    bars = ax.patches
    hs = []
    num_x = 2
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
        ax.bar_label(container, fmt="%.2f")

    plt.tight_layout()

    if outname is None:
        outname = f"nginx"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        outname += ".pdf"

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / outname
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")
