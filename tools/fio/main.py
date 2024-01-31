#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


mpl.use("Agg")
mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["font.family"] = "libertine"

# sns.set(rc={"figure.figsize": (5, 5)})
sns.set_style("whitegrid")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
sns.set_context("paper", rc={"font.size": 5, "axes.titlesize": 5, "axes.labelsize": 8})

palette = sns.color_palette("pastel")
hatches = ["", "/", "\\", "x", ".", "*", "o", "O", "+"]


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


def read_files(files, names=None):
    dfs = []
    for i, file in enumerate(files):
        data = read_json(file)
        if names is None:
            name = Path(file).stem
        else:
            name = names[i]
        df = process_data(data, name)
        dfs.append(df)
    df = pd.concat(dfs)
    return df


def plot_bw(df):
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
    for i, handle in enumerate(ax.get_legend().legend_handles[::-1]):
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

    ax.set(xticklabels=["seq read", "seq write"])

    # sns.move_legend(
    #     ax, "lower center",
    #     bbox_to_anchor=(.5, 0), ncol=3, title=None, frameon=True,
    # )

    plt.ylabel("Maximum Bandwidth [GiB/s]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    plt.savefig("bw.pdf")
    plt.clf()


def plot_iops(df):
    ## randread
    iops = df[(df["jobname"] == "iops randread")]
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
        x=x_coords[:n], y=y_coords[:n], yerr=iops["read_iops_stddev"], fmt="none", c="k"
    )
    ax.get_legend().set_title("")
    for i, bar in enumerate(ax.patches[:n]):
        bar.set_hatch(hatches[i])
    for i, handle in enumerate(ax.get_legend().legend_handles[::-1]):
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
        ncol=3,
        title=None,
        frameon=True,
    )

    ax.set(xticklabels=["readread", "randwrite"])
    # sns.despine()
    plt.ylabel("4KB Throughput [K IOPS]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    plt.savefig("iops.pdf")
    plt.clf()


def plot_latency(df):
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
    for i, handle in enumerate(ax.get_legend().legend_handles[::-1]):
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
        ncol=3,
        title=None,
        frameon=True,
    )

    ax.set(xticklabels=["read", "write", "randread", "randwrite"])
    plt.ylabel("4KB Latency [us]")
    plt.xlabel("")
    plt.title("Lower is better ↓", fontsize=9, color="navy", weight="bold")
    plt.savefig("latency.pdf")
    plt.clf()


def main():
    files = []
    names = []

    BASE = Path("/share/masa/cvm/backup/result/nvme1n1/inv-fio-logs/")

    files.append(
        BASE
        / "native-no-dmcrypt-aio-io_uring-8-nvme1n1-quick-fio-2024-01-30-20-04-34.log"
    )
    names.append("vm")
    files.append(
        BASE
        / "native-no-dmcrypt-aio-io_uring-8-nvme1n1-iouring-quick-fio-2024-01-30-20-44-11.log"
    )
    names.append("vm (poll)")
    files.append(
        BASE / "native-aio-io_uring-8-nvme1n1-quick-fio-2024-01-30-20-22-29.log"
    )
    names.append("vm w/ dm-crypt")

    files.append(
        BASE / "sev-no-dmcrypt-aio-io_uring-8-nvme1n1-quick-fio-2024-01-30-20-13-04.log"
    )
    names.append("sev")
    files.append(
        BASE
        / "sev-no-dmcrypt-aio-io_uring-8-nvme1n1-iouring-quick-fio-2024-01-30-20-52-56.log"
    )
    names.append("sev (poll)")
    files.append(BASE / "sev-aio-io_uring-8-nvme1n1-quick-fio-2024-01-30-20-32-02.log")
    names.append("sev w/ dm-crypt")

    df = read_files(files, names)
    print(df)

    plot_bw(df)
    plot_iops(df)
    plot_latency(df)

    pass


if __name__ == "__main__":
    main()
