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

BENCH_RESULT_DIR = Path("./bench-result/networking")


# bench mark path:
# ./bench-result/network/iperf/{name}/{date}
def parse_iperf_result(name: str, label: str, mode: str, date=None) -> pd.DataFrame:
    # create df like the following
    # | VM | pkt size | throughput |
    # |----|----------|------------|
    # |    |          |            |
    if mode == "udp":
        pktsize = [64, 128, 256, 512, 1024, 1460]
    elif mode == "tcp":
        pktsize = [64, 128, 256, 512, "1K", "32K", "128K"]
    else:
        raise ValueError(f"Invalid mode: {mode}")
    ths = []

    if date is None:
        # use the latest date
        date = sorted(os.listdir(BENCH_RESULT_DIR / "iperf" / name / mode))[-1]

    print(f"date: {date}")

    for size in pktsize:
        path = Path(f"./bench-result/networking/iperf/{name}/{mode}/{date}/{size}.log")
        if not path.exists():
            print(f"XXX: {path} not found!")
            continue
        with path.open("r") as f:
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

    print(ths)
    df = pd.DataFrame({"name": label, "size": pktsize[: len(ths)], "throughput": ths})
    return df


def parse_ping_result(name: str, label: str, date=None) -> pd.DataFrame:
    pktsize = [64, 128, 256, 512, 1024, 1460]
    # pktsize_actual = [56, 120, 248, 504, 1016, 1462]
    pktsize_actual = [64, 128, 256, 512, 1024, 1460]
    pktsize_ = []
    lats = []

    if date is None:
        # use the latest date
        date = sorted(os.listdir(BENCH_RESULT_DIR / "ping" / name))[-1]

    print(f"date: {date}")

    for size in pktsize_actual:
        path = Path(f"./bench-result/networking/ping/{name}/{date}/{size}.log")
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


@task
def plot_iperf(ctx, vm="amd", cvm="snp", mode="udp", outdir="plot"):
    df1 = parse_iperf_result(f"{vm}-direct-medium", vm, mode)
    df2 = parse_iperf_result(f"{cvm}-direct-medium", cvm, mode)
    # merge df using name as key
    df = pd.concat([df1, df2])

    # plot thropughput
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="size",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("Packet Size (byte)")
    ax.set_ylabel("Throughput (Gbps)")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

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
    for patch in ax.get_legend().get_patches()[1::2]:
        patch.set_hatch("//")

    # annotate values with .2f
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f")

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    save_path = outdir / f"iperf_{mode}_throughput.pdf"
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches="tight")
    print(f"Plot saved in {save_path}")


@task
def plot_ping(ctx, vm="amd", cvm="snp", outdir="plot", outname="ping.pdf"):
    df1 = parse_ping_result(f"{vm}-direct-medium", vm)
    df2 = parse_ping_result(f"{cvm}-direct-medium", cvm)
    # merge df using name as key
    df = pd.concat([df1, df2])
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
    )
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
