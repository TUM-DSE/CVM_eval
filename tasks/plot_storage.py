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
#hatches = ["", "//", "x", "//x"]
hatches = ["", "", "//"]


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


def read_result(name: str, label: str, jobname: str, date=None) -> pd.DataFrame:
    if date is None:
        # use the latest one
        date = Path(sorted(os.listdir(BENCH_RESULT_DIR / name / jobname))[-1]).stem

    file = BENCH_RESULT_DIR / name / jobname / f"{date}.json"
    print(f"file: {file}")
    data = read_json(file)
    df = process_data(data, label)

    return df


def plot_bw(df, outdir, device=""):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    # read
    bw = df[(df["jobname"] == "bw read")]
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
    bw = df[(df["jobname"] == "bw write")]
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
        bbox_to_anchor=(0.5, 0),
        ncol=5,
        title=None,
        frameon=True,
    )

    plt.ylabel("Maximum Bandwidth [GiB/s]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    plt.tight_layout()
    outfile = Path(outdir) / f"fio_bw_{device}.pdf"
    plt.savefig(outfile, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"saved to {outfile}")
    plt.clf()


def plot_iops(df, outdir, device=""):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    ## randread
    iops = df[(df["jobname"] == "iops randread")]
    ax = sns.barplot( data=iops,
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
        x=x_coords[:n], y=y_coords[:n], yerr=iops["read_iops_stddev"], fmt="none", c="k"
    )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles):
        handle.set_hatch(hatches[i])

    ## randwrite
    iops = df[(df["jobname"] == "iops randwrite")]
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
    )

    ## mixread70
    iops = df[(df["jobname"] == "iops rwmixread")]
    iops["iops_mean"] = iops["read_iops_mean"] + iops["write_iops_mean"]
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )

    ## mixread30
    iops = df[(df["jobname"] == "iops rwmixwrite")]
    iops["iops_mean"] = iops["read_iops_mean"] + iops["write_iops_mean"]
    ax = sns.barplot(
        data=iops,
        x="jobname",
        y="iops_mean",
        hue="name",
        palette=palette,
        edgecolor="k",
        linewidth=1.0,
        legend=False,
    )

    # apply hatch
    for i, bar in enumerate(ax.patches[n * 2 :]):
        bar.set_hatch(hatches[i % n])

    # put numbers on top of bars
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        if height == 0.0:
            continue
        ax.text(
            x=p.get_x() + p.get_width() / 2.0,
            y=height + 2000,
            s=f"{height/1000:.2f}",
            ha="center",
        )

    ax.yaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda val, pos: f"{val/1000:g}")
    )

    sns.move_legend(
        ax,
        "lower center",
        bbox_to_anchor=(0.5, 0),
        ncol=5,
        title=None,
        frameon=True,
    )

    # ax.set(xticklabels=["readread", "randwrite", "mixread70",
    #                     "mixread30"])
    # ax.set_xticklabels(["Randread", "Randwrite", "Mixrw(read70)",
    #                     "Mixrw(read30)"], rotation=45)
    ax.set_xticklabels(["RandR", "RandW", "RRW70", "RRW30"], rotation=30)
    # sns.despine()
    plt.ylabel("4KB Throughput [K IOPS]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    plt.tight_layout()
    outfile = Path(outdir) / f"fio_iops_{device}.pdf"
    plt.savefig(outfile, format="pdf", pad_inches=0, bbox_inches="tight")
    print(f"saved to {outfile}")
    plt.clf()


def plot_latency(df, outdir, device=""):
    fig, ax = plt.subplots(figsize=(figwidth_half, 2.5))

    ## read
    lat = df[(df["jobname"] == "alat read")]
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
    lat = df[(df["jobname"] == "alat write")]
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
    lat = df[(df["jobname"] == "alat randread")]
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
    lat = df[(df["jobname"] == "alat randwrite")]
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
            s=f"{height/1000:.2f}",
            ha="center",
        )

    sns.move_legend(
        ax,
        "lower center",
        bbox_to_anchor=(0.5, -0.0),
        ncol=5,
        title=None,
        frameon=True,
    )

    # ax.set(xticklabels=["read", "write", "randread", "randwrite"], rotation=90)
    # ax.set_xticklabels(["Read", "Write", "Randread", "Randwrite"], rotation=45)
    ax.set_xticklabels(["Read", "Write", "RandR", "RandW"], rotation=30)
    plt.ylabel("4KB Latency [us]")
    plt.xlabel("")
    plt.title("Lower is better ↓", fontsize=9, color="navy", weight="bold")
    plt.tight_layout()
    outfile = Path(outdir) / f"fio_latency_{device}.pdf"
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

    vm_data = read_result(f"{vm}-direct-{size}{device}-{aio}", vm_label, jobfile)
    swiotlb_data = read_result(f"{vm}-direct-{size}{device}-{aio}-swiotlb", "swiotlb", jobfile)
    cvm_data = read_result(f"{cvm}-direct-{size}{device}-{aio}", cvm_label, jobfile)

    # labels = [vm, "swiotlb", cvm]
    # labels = ["vm", "swiotlb", "td"]
    #labels = ["vm", "swiotlb", "td", "td-poll"]
    # df = pd.concat([vm_data, swiotlb_data, cvm_data])
    #df = pd.concat([vm_data, swiotlb_data, cvm_data, cvm_poll_data])
    df = pd.concat([vm_data, swiotlb_data, cvm_data])
    print(df)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    plot_bw(df, outdir, device)
    plot_iops(df, outdir, device)
    plot_latency(df, outdir, device)
