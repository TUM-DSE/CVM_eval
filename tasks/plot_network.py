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
#hatches = ["", "//"]
hatches = ["", "", "", "", "//", "////"]

BENCH_RESULT_DIR = Path("./bench-result/network")


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
        pktsize = [64, 128, 256, 512, 1024, "32K", "128K"]
    else:
        raise ValueError(f"Invalid mode: {mode}")
    ths = []

    if date is None:
        # use the latest date
        date = sorted(os.listdir(BENCH_RESULT_DIR / "iperf" / name / mode))[-1]

    print(f"date: {date}")

    for size in pktsize:
        path = Path(f"./bench-result/network/iperf/{name}/{mode}/{date}/{size}.log")
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
    name: str, label: str, server: str, date=None, date_tls=None
) -> pd.DataFrame:
    if date is None:
        date = sorted(os.listdir(BENCH_RESULT_DIR / "memtier" / server / name))[-1]
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

    df = pd.concat([df, df_tls])

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


def parse_nginx_result(name: str, label: str, date=None) -> pd.DataFrame:
    if date is None:
        date = sorted(os.listdir(BENCH_RESULT_DIR / "nginx" / name))[-1]

    df = parse_nginx_result_sub(
        BENCH_RESULT_DIR / "nginx" / name / date / "http.log",
        label,
        "http",
    )
    df_ssl = parse_nginx_result_sub(
        BENCH_RESULT_DIR / "nginx" / name / date / "https.log",
        label,
        "https",
    )

    df = pd.concat([df, df_ssl])

    return df


@task
def plot_iperf(
    ctx,
    cvm="snp",
    mode="udp",
    vhost=False,
    mq=False,
    outdir="plot",
    outname=None,
    size="medium",
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    def get_name(name, vhost=False, mq=mq, swiotlb=False):
        n = f"{name}-direct-{size}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        if swiotlb:
            n += "-swiotlb"
        return n

    #df1 = parse_iperf_result(get_name(vm), vm, mode)
    #df2 = parse_iperf_result(get_name(cvm), cvm, mode)
    ## merge df using name as key
    #df = pd.concat([df1, df2])

    dfs = []
    dfs.append(parse_iperf_result(get_name(vm), vm_label, mode))
    dfs.append(parse_iperf_result(get_name(vm, vhost=False, swiotlb=True), f"swiotlb", mode))
    dfs.append(parse_iperf_result(get_name(vm, vhost=True), f"vhost", mode))
    dfs.append(parse_iperf_result(get_name(vm, vhost=True, swiotlb=True), f"vhost-swiotlb", mode))
    dfs.append(parse_iperf_result(get_name(cvm), cvm_label, mode))
    dfs.append(parse_iperf_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost", mode))
    df = pd.concat(dfs)
    print(df)

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
        ax.bar_label(container, fmt="%.2f", fontsize=5)

    plt.tight_layout()
    plt.legend(fontsize=5)

    if outname is None:
        outname = f"iperf_{mode}"
        if vhost:
            outname += "_vhost"
        if mq:
            outname += "_mq"
        outname += "_throughput.pdf"

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
    outdir="plot",
    outname=None,
    size="medium",
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    def get_name(name, vhost=False, mq=mq, swiotlb=False):
        n = f"{name}-direct-{size}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        if swiotlb:
            n += "-swiotlb"
        return n

    dfs = []
    dfs.append(parse_ping_result(get_name(vm), vm_label))
    dfs.append(parse_ping_result(get_name(vm, vhost=False, swiotlb=True), f"swiotlb"))
    dfs.append(parse_ping_result(get_name(vm, vhost=True), f"vhost"))
    dfs.append(parse_ping_result(get_name(vm, vhost=True, swiotlb=True), f"vhost-swiotlb"))
    dfs.append(parse_ping_result(get_name(cvm), cvm_label))
    dfs.append(parse_ping_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost"))
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
    plt.legend(fontsize=5)

    if outname is None:
        outname = f"ping"
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
def plot_redis(
    ctx,
    cvm="snp",
    vhost=False,
    mq=False,
    outdir="plot",
    outname=None,
    size="medium",
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    def get_name(name, vhost=False, mq=mq):
        n = f"{name}-direct-{size}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_memtier_result(get_name(vm), vm_label, "redis"))
    dfs.append(parse_memtier_result(get_name(vm, vhost=True), f"vhost", "redis"))
    dfs.append(parse_memtier_result(get_name(cvm), cvm_label, "redis"))
    dfs.append(parse_memtier_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost", "redis"))
    df = pd.concat(dfs)
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = 4
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
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    def get_name(name, vhost=False, mq=mq):
        n = f"{name}-direct-{size}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_memtier_result(get_name(vm), vm_label, "memcached"))
    dfs.append(parse_memtier_result(get_name(vm, vhost=True), f"vhost", "memcached"))
    dfs.append(parse_memtier_result(get_name(cvm), cvm_label, "memcached"))
    dfs.append(parse_memtier_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost", "memcached"))
    df = pd.concat(dfs)
    print(df)

    fig, ax = plt.subplots(figsize=(figwidth_half, 2.0))
    sns.barplot(
        x="workload",
        y="throughput",
        hue="name",
        data=df,
        ax=ax,
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = 4
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
):
    if cvm == "snp":
        vm = "amd"
        vm_label = "vm"
        cvm_label = "snp"
    else:
        vm = "intel"
        vm_label = "vm"
        cvm_label = "td"

    def get_name(name, vhost=False, mq=mq):
        n = f"{name}-direct-{size}"
        if vhost:
            n += "-vhost"
        if mq:
            n += "-mq"
        return n

    dfs = []
    dfs.append(parse_nginx_result(get_name(vm), vm_label))
    dfs.append(parse_nginx_result(get_name(vm, vhost=True), f"vhost"))
    dfs.append(parse_nginx_result(get_name(cvm), cvm_label))
    dfs.append(parse_nginx_result(get_name(cvm, vhost=True), f"{cvm_label}-vhost"))
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
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Throughput [M req/s]")
    ax.set_title("Higher is better ↑", fontsize=FONTSIZE, color="navy")

    # remove legend title
    ax.get_legend().set_title("")

    # set hatch
    bars = ax.patches
    hs = []
    num_x = 2
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
