#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Union

from invoke import task
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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
swiotlb_col = pastel[1]
cvm_col = pastel[2]
palette = [vm_col, swiotlb_col, cvm_col]
# hatches = ["", "//", "x", "//x"]
hatches = ["", "o", "//", "x", ""]


def read_json(file):
    lines = []
    with open(file) as f:
        # ignore error massages if any
        # (skip line until "{" is found)
        for line in f:
            if line.strip() == "{":
                lines.append(line)
                break
            else:
                print(f"[warn] skipping line: {line.strip()}")
        for line in f:
            lines.append(line)
    data = json.loads("".join(lines))
    return data


def process_data(data, name):
    d = []
    for job in data["jobs"]:
        d.append(
            [
                name,
                job["jobname"],
                float(job["read"]["iops_mean"]),
                float(job["read"]["iops_stddev"]),
                float(job["read"]["bw_mean"]),
                float(job["read"]["bw_dev"]),
                float(job["read"]["lat_ns"]["mean"]),
                float(job["read"]["lat_ns"]["stddev"]),
                float(job["write"]["iops_mean"]),
                float(job["write"]["iops_stddev"]),
                float(job["write"]["bw_mean"]),
                float(job["write"]["bw_dev"]),
                float(job["write"]["lat_ns"]["mean"]),
                float(job["write"]["lat_ns"]["stddev"]),
            ]
        )
    columns = [
        "name",
        "jobname",
        "read_iops_mean",
        "read_iops_stddev",
        "read_bw_mean",
        "read_bw_dev",
        "read_lat_mean",
        "read_lat_dev",
        "write_iops_mean",
        "write_iops_stddev",
        "write_bw_mean",
        "write_bw_dev",
        "write_lat_mean",
        "write_lat_dev",
    ]
    df = pd.DataFrame(d, columns=columns)
    return df


BENCH_RESULT_DIR = Path("./bench-result/fio")


def read_result(
    name: str, label: str, jobname: str, date=None, max_num: int = 10
) -> pd.DataFrame:
    dates = []
    if date is None:
        # use the latest results
        # note: fio reports stddev
        dates = [
            Path(i).stem
            for i in sorted(os.listdir(BENCH_RESULT_DIR / name / jobname))[-max_num:]
        ]
    else:
        dates.append(date)

    dfs = []
    for date in dates:
        file = BENCH_RESULT_DIR / name / jobname / f"{date}.json"
        data = read_json(file)
        df = process_data(data, label)
        dfs.append(df)

    # merge df
    df = pd.concat(dfs)

    return df


def plot_bw(df, outdir, outname, legend=True):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    # read
    bw = df[(df["jobname"] == "bw read")].reset_index()
    ## select median
    names = bw["name"].unique()
    dfs = []
    for name in names:
        ranks = bw[bw["name"] == name]["read_bw_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = bw.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    bw = pd.concat(dfs)

    # get meaidn values of read_bw_mean
    ax = sns.barplot(
        data=bw,
        x="jobname",
        y="read_bw_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    n = len(x_coords) // 2
    ax.errorbar(
        x=x_coords[:n], y=y_coords[:n], yerr=bw["read_bw_dev"], fmt="none", c="k"
    )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ## write
    bw = df[(df["jobname"] == "bw write")].reset_index()
    # select median
    names = bw["name"].unique()
    dfs = []
    for name in names:
        ranks = bw[bw["name"] == name]["write_bw_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = bw.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    bw = pd.concat(dfs)
    ax = sns.barplot(
        data=bw,
        x="jobname",
        y="write_bw_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[n * 2 :],
        y=y_coords[n * 2 :],
        yerr=bw["write_bw_dev"],
        fmt="none",
        c="k",
        elinewidth=1,
    )
    # apply hatch
    for i, bar in enumerate(ax.patches[n * 2 :]):
        bar.set_hatch(hatches[i])

    # put numbers on top of bars
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        if height == 0.0:
            continue
        ax.text(
            x=p.get_x() + p.get_width() / 2.0,
            y=height + 100000,
            s=f"{height/1_000_000:.2f}",
            ha="center",
        )

    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda val, pos: f"{val/1_000_000:g}")
    )

    # ax.set(xticklabels=["seq read", "seq write"])
    ax.set_xticklabels(["Read", "Write"], rotation=30)

    sns.move_legend(
        ax,
        "lower center",
        # bbox_to_anchor=(0.5, 0),
        ncol=5,
        title=None,
        frameon=True,
    )

    if not legend:
        plt.legend([],[], frameon=False)

    # plt.ylabel("Maximum Bandwidth [GiB/s]")
    plt.ylabel("Bandwidth [GiB/s]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    sns.despine(top = True)
    plt.tight_layout()
    outfile = Path(outdir) / outname
    plt.savefig(outfile, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"saved to {outfile}")
    plt.clf()


def plot_iops(df, outdir, outname="", legend=True):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    ## randread
    iops = df[(df["jobname"] == "iops randread")].reset_index()
    ## select median
    names = iops["name"].unique()
    dfs = []
    for name in names:
        ranks = iops[iops["name"] == name]["read_iops_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = iops.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    iops = pd.concat(dfs)
    print(iops)
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="read_iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=True,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    n = len(x_coords) // 2
    ax.errorbar(
        x=x_coords[:n],
        y=y_coords[:n],
        yerr=iops["read_iops_stddev"],
        fmt="none",
        c="k",
        elinewidth=0.8,
    )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ## randwrite
    iops = df[(df["jobname"] == "iops randwrite")].reset_index()
    ## select median
    names = iops["name"].unique()
    dfs = []
    for name in names:
        ranks = iops[iops["name"] == name]["write_iops_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = iops.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    iops = pd.concat(dfs)
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="write_iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[n * 2 :],
        y=y_coords[n * 2 :],
        yerr=iops["write_iops_stddev"],
        fmt="none",
        c="k",
        elinewidth=0.8,
    )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ## mixread70
    iops = df[(df["jobname"] == "iops rwmixread")].reset_index()
    # create table with read_iops_mean + write_iops_mean
    iops["iops_mean"] = iops["read_iops_mean"] + iops["write_iops_mean"]
    ## select median
    names = iops["name"].unique()
    dfs = []
    for name in names:
        ranks = iops[iops["name"] == name]["iops_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = iops.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    iops = pd.concat(dfs)
    # plot read_iops_mean
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="iops_mean",
        # y="read_iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    # sns.barplot(
    #    data=iops,
    #    x="jobname",
    #    y="write_iops_mean",
    #    hue="name",
    #    palette=palette,
    #    edgecolor="k",
    #    linewidth=1.0,
    #    legend=False,
    #    bottom=iops["read_iops_mean"],
    # )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ## mixread30
    iops = df[(df["jobname"] == "iops rwmixwrite")].reset_index()
    iops["iops_mean"] = iops["read_iops_mean"] + iops["write_iops_mean"]
    iops.reset_index()
    ## select median
    names = iops["name"].unique()
    dfs = []
    for name in names:
        ranks = iops[iops["name"] == name]["iops_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = iops.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    iops = pd.concat(dfs)
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="iops_mean",
        # y="read_iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    # sns.barplot(
    #    data=iops,
    #    x="jobname",
    #    y="write_iops_mean",
    #    hue="name",
    #    palette=palette,
    #    edgecolor="k",
    #    linewidth=1.0,
    #    legend=False,
    #    bottom=iops["read_iops_mean"],
    # )
    i = 0
    while i < len(ax.patches):
        j = 0
        for j in range(n):
            ax.patches[i + j].set_hatch(hatches[j])
        i += n

    # apply hatch
    # for i, bar in enumerate(ax.patches[n * 2 :]):
    #    bar.set_hatch(hatches[i % n])

    # put numbers on top of bars
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        if height == 0.0:
            continue
        ax.text(
            x=p.get_x() + p.get_width() / 2.0,
            y=height + 2000,
            #s=f"{height/1000:.2f}",
            s=f"{height/1000:.0f}",
            ha="center",
            #rotation=90,
        )

    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda val, pos: f"{val/1000:g}")
    )

    sns.move_legend(
        ax,
        "lower center",
        # bbox_to_anchor=(0.5, 0),
        ncol=5,
        title=None,
        frameon=True,
    )

    if not legend:
        plt.legend([],[], frameon=False)

    # ax.set(xticklabels=["readread", "randwrite", "mixread70",
    #                     "mixread30"])
    # ax.set_xticklabels(["Randread", "Randwrite", "Mixrw(read70)",
    #                     "Mixrw(read30)"], rotation=45)
    ax.set_xticklabels(["RandR", "RandW", "RRW70", "RRW30"], rotation=30)
    # sns.despine()
    #plt.ylabel("4KB Throughput [K IOPS]")
    plt.ylabel("Throughput [K IOPS]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    sns.despine(top = True)
    plt.tight_layout()
    outfile = Path(outdir) / outname
    plt.savefig(outfile, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"saved to {outfile}")
    plt.clf()


def plot_latency(df, outdir, outname, legend=True):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    ## read
    lat = df[(df["jobname"] == "alat read")].reset_index()
    ## select median
    names = lat["name"].unique()
    dfs = []
    for name in names:
        ranks = lat[lat["name"] == name]["read_lat_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = lat.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    lat = pd.concat(dfs)
    ax = sns.barplot(
        data=lat,
        x="jobname",
        y="read_lat_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=True,
    )
    ax.get_legend().set_title("")
    n = len(ax.patches) // 2
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[:n], y=y_coords[:n], yerr=lat["read_lat_dev"], fmt="none", c="k"
    )

    ## write
    lat = df[(df["jobname"] == "alat write")].reset_index()
    ## select median
    names = lat["name"].unique()
    dfs = []
    for name in names:
        ranks = lat[lat["name"] == name]["write_lat_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = lat.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    lat = pd.concat(dfs)
    ax = sns.barplot(
        data=lat,
        x="jobname",
        y="write_lat_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[n * 2 :],
        y=y_coords[n * 2 :],
        yerr=lat["write_lat_dev"],
        fmt="none",
        c="k",
    )

    ## randread
    lat = df[(df["jobname"] == "alat randread")].reset_index()
    ## select median
    names = lat["name"].unique()
    dfs = []
    for name in names:
        ranks = lat[lat["name"] == name]["read_lat_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = lat.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    lat = pd.concat(dfs)
    ax = sns.barplot(
        data=lat,
        x="jobname",
        y="read_lat_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[n * 3 :],
        y=y_coords[n * 3 :],
        yerr=lat["read_lat_dev"],
        fmt="none",
        c="k",
    )

    ## randwrite
    lat = df[(df["jobname"] == "alat randwrite")].reset_index()
    ## select median
    names = lat["name"].unique()
    dfs = []
    for name in names:
        ranks = lat[lat["name"] == name]["write_lat_mean"].rank(pct=True)
        close_to_median = abs(ranks - 0.5)
        idx = close_to_median.idxmin()
        a = lat.loc[idx]
        a = pd.DataFrame(a).T
        dfs.append(a)
    lat = pd.concat(dfs)
    ax = sns.barplot(
        data=lat,
        x="jobname",
        y="write_lat_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )
    h, l = ax.get_legend_handles_labels()
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[n * 4 :],
        y=y_coords[n * 4 :],
        yerr=lat["write_lat_dev"],
        fmt="none",
        c="k",
    )
    for i, bar in enumerate(ax.patches):
        bar.set_hatch(hatches[i % n])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda val, pos: f"{val/1000:g}")
    )

    # put numbers on top of bars
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        if height == 0.0:
            continue
        ax.text(
            x=p.get_x() + p.get_width() / 2.0,
            y=height + 2000,
            #s=f"{height/1000:.2f}",
            s=f"{height/1000:.0f}",
            ha="center",
            #rotation=90,
        )

    sns.move_legend(
        ax,
        "upper center",
        # bbox_to_anchor=(0.5, -0.0),
        ncol=3,
        title=None,
        frameon=True,
    )

    if not legend:
        plt.legend([],[], frameon=False)

    # ax.set(xticklabels=["read", "write", "randread", "randwrite"], rotation=90)
    # ax.set_xticklabels(["Read", "Write", "Randread", "Randwrite"], rotation=45)
    ax.set_xticklabels(["Read", "Write", "RandR", "RandW"], rotation=30)
    plt.ylabel("4KB Latency [us]")
    plt.xlabel("")
    plt.title("Lower is better ↓", fontsize=9, color="navy", weight="bold")
    sns.despine(top = True)
    plt.tight_layout()
    outfile = Path(outdir) / outname
    plt.savefig(outfile, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"saved to {outfile}")
    plt.clf()


@task
def plot_fio(
    ctx: Any,
    cvm="snp",
    size="medium",
    aio="native",
    jobfile="libaio",
    outdir="plot",
    device="nvme1n1",
    tmebypass=False,
    poll=False,
    all=False,
    swiotlb=True,
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

    dfs = []
    dfs.append(
        read_result(f"{vm}-direct-{size}-{device}{pvm}-{aio}", vm_label, jobfile)
    )
    if swiotlb and not poll:
        dfs.append(
            read_result(
                f"{vm}-direct-{size}-{device}-{aio}{pvm}-swiotlb", "swiotlb", jobfile
            )
        )
    dfs.append(
        read_result(f"{cvm}-direct-{size}-{device}{pcvm}-{aio}", cvm_label, jobfile)
    )
    if all:
        dfs.append(
            read_result(
                f"{cvm}-direct-{size}-{device}-poll-{aio}", f"{cvm_label}-poll", jobfile
            )
        )
        #dfs.append(
        #    read_result(
        #        f"{vm}-direct-{size}-{device}-poll-{aio}", f"{vm_label}-poll", jobfile
        #    )
        #)

    df = pd.concat(dfs)
    print(df)
    # save df
    df.to_csv(Path(outdir) / f"fio_{device}{pvm}.csv", index=False)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if all:
        pvm += "-all"
    plot_bw(df, outdir, f"fio_bw_{device}{pvm}.pdf", legend=True)
    plot_iops(df, outdir, f"fio_iops_{device}{pvm}.pdf", legend=False)
    plot_latency(df, outdir, f"fio_latency_{device}{pvm}.pdf", legend=False)


@task
def analyze_fio(
    ctx: Any,
    cvm="snp",
    size="medium",
    aio="native",
    jobfile="libaio",
    outdir="plot",
    device="nvme1n1",
    tmebypass=False,
    poll=False,
    swiotlb=False,
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

    df = read_result(
        f"{vm}-direct-{size}-{device}{pvm}-{aio}", vm_label, jobfile, max_num=10
    )
    cdf = read_result(
        f"{cvm}-direct-{size}-{device}{pcvm}-{aio}", cvm_label, jobfile, max_num=10
    )

    print(df[(df["jobname"] == "bw read")]["read_bw_mean"])
    print(cdf[(cdf["jobname"] == "bw read")]["read_bw_mean"])

    print(df[(df["jobname"] == "bw write")]["write_bw_mean"])
    print(cdf[(cdf["jobname"] == "bw write")]["write_bw_mean"])

    print(df[(df["jobname"] == "iops randread")]["read_iops_mean"])
    print(cdf[(cdf["jobname"] == "iops randread")]["read_iops_mean"])

    print(df[(df["jobname"] == "iops randwrite")]["write_iops_mean"])
    print(cdf[(cdf["jobname"] == "iops randwrite")]["write_iops_mean"])
