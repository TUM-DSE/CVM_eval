#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path
import glob

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import colorama
from colorama import Back, Fore, Style

colorama.init()

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
hatches = [
    "",
    "/",
    "\\",
    "x",
    ".",
    "*",
    "o",
    "O",
    "+",
    "//",
    "\\\\",
    "||",
    "--",
    "++",
    "xx",
    "oo",
    "OO",
    "..",
    "**",
    "/o",
    "\\|",
    "|*",
    "-\\",
    "+o",
    "x*",
    "o-",
    "O|",
    "O.",
    "*-",
]


def warn_print(msg: str) -> None:
    print(Style.BRIGHT + Back.CYAN + Fore.LIGHTRED_EX + f"[WARN]: {msg}")
    print(Style.RESET_ALL)


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
                warn_print(f"skipping line: {line.strip()}")
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


def plot_bw(df, basedir="."):
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

    ax.set(xticklabels=["seq read", "seq write"])

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
    plt.savefig(Path(basedir) / "bw.pdf")
    plt.clf()


def plot_iops(df, basedir="."):
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
        ncol=5,
        title=None,
        frameon=True,
    )

    ax.set(xticklabels=["readread", "randwrite"])
    # sns.despine()
    plt.ylabel("4KB Throughput [K IOPS]")
    plt.xlabel("")
    plt.title("Higher is better ↑", fontsize=9, color="navy", weight="bold")
    plt.savefig(Path(basedir) / "iops.pdf")
    plt.clf()


def plot_latency(df, basedir="."):
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

    ax.set(xticklabels=["read", "write", "randread", "randwrite"])
    plt.ylabel("4KB Latency [us]")
    plt.xlabel("")
    plt.title("Lower is better ↓", fontsize=9, color="navy", weight="bold")
    plt.savefig(Path(basedir) / "latency.pdf")
    plt.clf()


def find_file(BASE, name):
    path = str(Path(BASE) / name)
    files = glob.glob(path)
    if len(files) != 1:
        warn_print(f"{path}:  {files}")
        if len(files) == 0:
            raise Exception("file not found")
    return files[0]


def main(BASE, nvme="nvme1n1"):
    files = []
    names = []

    files.append(
        find_file(BASE, f"native-no-dmcrypt-aio-io_uring-8-{nvme}-quick-fio-*.log")
    )
    names.append("vm")
    files.append(
        find_file(
            BASE, f"native-no-dmcrypt-aio-io_uring-8-{nvme}-iouring-quick-fio-*.log"
        )
    )
    names.append("vm (poll)")
    files.append(find_file(BASE, f"native-aio-io_uring-8-{nvme}-quick-fio-*.log"))
    names.append("vm w/ dm-crypt")

    files.append(
        find_file(BASE, f"sev-no-dmcrypt-aio-io_uring-8-{nvme}-quick-fio-*.log")
    )
    names.append("sev")
    files.append(
        find_file(BASE, f"sev-no-dmcrypt-aio-io_uring-8-{nvme}-iouring-quick-fio-*.log")
    )
    names.append("sev (poll)")
    files.append(find_file(BASE, f"sev-aio-io_uring-8-{nvme}-quick-fio-*.log"))
    names.append("sev w/ dm-crypt")

    df = read_files(files, names)
    print(df)

    plot_bw(df)
    plot_iops(df)
    plot_latency(df)


def main2(BASE, no_dm_crypt=True, dm_crypt=False, outdir=".", ignore_errors=True):
    files = []
    names = []

    def try_add(name, pattern):
        try:
            files.append(find_file(BASE, pattern))
            names.append(name)
        except:
            if not ignore_errors:
                raise

    if no_dm_crypt:
        try_add("libaio", f"native-no-dmcrypt-*-libaio-*.log")
        try_add("iou", f"native-no-dmcrypt-*-iou-*.log")
        try_add("iou-s", f"native-no-dmcrypt-*-iou_s-*.log")
        try_add("iou-c", f"native-no-dmcrypt-*-iou_c-*.log")
        try_add("iou-sc", f"native-no-dmcrypt-*-iou_sc-*.log")

    if dm_crypt:
        try_add("libaio*", f"native-aio-*-libaio-*.log")
        try_add("iou*", f"native-aio-*-iou-*.log")
        try_add("iou_s*", f"native-aio-*-iou_s-*.log")
        # try_add("iou_c*", f"native-aio-*-iou_c-*.log")
        # try_add("iou_sc*", f"native-aio-*-iou_sc-*.log")

    if no_dm_crypt:
        try_add("sev libaio", f"sev-no-dmcrypt-*-libaio-*.log")
        try_add("sev iou", f"sev-no-dmcrypt-*-iou-*.log")
        try_add("sev iou_s", f"sev-no-dmcrypt-*-iou_s-*.log")
        try_add("sev iou_c", f"sev-no-dmcrypt-*-iou_c-*.log")
        try_add("sev iou_sc", f"sev-no-dmcrypt-*-iou_sc-*.log")

    if dm_crypt:
        try_add("sev libaio*", f"sev-aio-*-libaio-*.log")
        try_add("sev iou*", f"sev-aio-*-iou-*.log")
        try_add("sev iou_s*", f"sev-aio-*-iou_s-*.log")
        # try_add("sev iou_c*", f"sev-aio-*-iou_c-*.log")
        # try_add("sev iou_sc*", f"sev-aio-*-iou_sc-*.log")

    df = read_files(files, names)
    print(df)

    # create outdir if not exist
    Path(outdir).mkdir(parents=True, exist_ok=True)

    plot_bw(df, outdir)
    plot_iops(df, outdir)
    plot_latency(df, outdir)


def main3(BASE, outdir=".", ignore_errors=True):
    files = []
    names = []

    def try_add(name, pattern):
        try:
            files.append(find_file(BASE, pattern))
            names.append(name)
        except:
            if not ignore_errors:
                raise

    try_add("native", f"native-no-dmcrypt-*-long-io_uring-*.log")
    try_add("native*", f"native-aio-*-long-io_uring-*.log")
    try_add("tdx", f"tdx-no-dmcrypt-*-long-io_uring-*.log")
    try_add("tdx*", f"tdx-aio-*-long-io_uring-*.log")

    df = read_files(files, names)
    print(df)

    # create outdir if not exist
    Path(outdir).mkdir(parents=True, exist_ok=True)

    # plot_bw(df, outdir)
    plot_iops(df, outdir)
    # plot_latency(df, outdir)


if __name__ == "__main__":
    # main("/share/masa/cvm/backup/result/nvme1n1/cvm-io/inv-fio-logs/")
    # main("/share/masa/cvm/backup/result/nvme1n1/force-swiotlb/inv-fio-logs")
    # main("/share/masa/cvm/backup/result/nvme1n1/virtio-scsi/inv-fio-logs")

    main3("/scratch/robert/tdx-logs", outdir="./plot/tdx")
    sys.exit(0)

    # main2("/share/masa/cvm/backup/result/new/virtio-blk/inv-fio-logs/")

    def plot_all(base, outdir):
        main2(base, no_dm_crypt=True, dm_crypt=True, outdir=Path(outdir) / "all")
        main2(
            base, no_dm_crypt=True, dm_crypt=False, outdir=Path(outdir) / "no_dm_crypt"
        )
        main2(base, no_dm_crypt=False, dm_crypt=True, outdir=Path(outdir) / "dm_crypt")

    # plot_all(
    #    "/share/masa/cvm/backup/result/new/virtio-blk/inv-fio-logs/",
    #    outdir="./plot/virtio-blk/nvme1",
    # )
    # plot_all(
    #    "/share/masa/cvm/backup/result/new/virtio-blk/nvme2/inv-fio-logs",
    #    outdir="./plot/virtio-blk/nvme2",
    # )
    # plot_all(
    #    "/share/masa/cvm/backup/result/new/virtio-scsi/inv-fio-logs",
    #    outdir="./plot/virtio-scsi/nvme1",
    # )
    # plot_all(
    #    "/share/masa/cvm/backup/result/new/virtio-scsi/nvme2/inv-fio-logs",
    #    outdir="./plot/virtio-scsi/nvme2",
    # )
    plot_all(
        "/share/masa/cvm/backup/result/new/virtio-blk/vcpu12/inv-fio-logs",
        outdir="./plot/virtio-blk/nvme1/vcpu12/",
    )
