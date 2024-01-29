#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


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


def read_files(files):
    dfs = []
    for file in files:
        data = read_json(file)
        name = Path(file).stem
        df = process_data(data, name)
        dfs.append(df)
    df = pd.concat(dfs)
    return df


def plot_bw(df):
    ## read
    bw = df[(df["jobname"] == "bw read")]
    bw = bw.groupby(["name"]).sum().reset_index()
    ax = sns.barplot(data=bw, x="jobname", y="read_bw_mean", hue="name")
    hue_labels = ["native", "sev"]
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, hue_labels, title="")
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[:2], y=y_coords[:2], yerr=bw["read_bw_dev"], fmt="none", c="k"
    )

    ## write
    bw = df[(df["jobname"] == "bw write")]
    bw = bw.groupby(["name"]).sum().reset_index()
    ax = sns.barplot(data=bw, x="jobname", y="write_bw_mean", hue="name")
    hue_labels = ["native", "sev"]
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, hue_labels, title="")
    x_coords = [p.get_x() + 0.5 * p.get_width() for p in ax.patches]
    y_coords = [p.get_height() for p in ax.patches]
    ax.errorbar(
        x=x_coords[4:6], y=y_coords[4:6], yerr=bw["write_bw_dev"], fmt="none", c="k"
    )

    plt.ylabel("Bandwidth")
    plt.savefig("bw.pdf")
    plt.clf()


def plot_iops(df):
    ## randread
    iops = df[(df["jobname"] == "iops randread")]
    iops = iops.groupby(["name"]).sum().reset_index()
    ax = sns.barplot(data=iops, x="jobname", y="read_iops_mean", hue="name")
    ax.set(xticklabels=[])

    ## randwrite
    iops = df[(df["jobname"] == "iops randwrite")]
    iops = iops.groupby(["name"]).sum().reset_index()
    ax = sns.barplot(data=iops, x="jobname", y="write_iops_mean", hue="name")
    ax.set(xticklabels=["randread", "randwrite"])
    hue_labels = ["native", "sev"]
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, hue_labels, title="")

    plt.ylabel("Mean IOPS")
    plt.savefig("iops.pdf")
    plt.clf()


def plot_latency(df):
    ## read
    lat = df[(df["jobname"] == "alat read")]
    ax = sns.barplot(data=lat, x="jobname", y="read_lat_mean", hue="name")
    ax.set(xticklabels=[])

    ## write
    lat = df[(df["jobname"] == "alat write")]
    ax = sns.barplot(data=lat, x="jobname", y="write_lat_mean", hue="name")
    ax.set(xticklabels=[])

    ## randread
    lat = df[(df["jobname"] == "alat randread")]
    ax = sns.barplot(data=lat, x="jobname", y="read_lat_mean", hue="name")
    ax.set(xticklabels=[])

    ## randwrite
    lat = df[(df["jobname"] == "alat randwrite")]
    ax = sns.barplot(data=lat, x="jobname", y="write_lat_mean", hue="name")
    ax.set(xticklabels=["read", "write", "randread", "randwrite"])
    hue_labels = ["native", "sev"]
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, hue_labels, title="")

    plt.ylabel("Mean Latency")
    plt.savefig("latency.pdf")
    plt.clf()


def main(files):
    df = read_files(files)

    plot_bw(df)
    plot_iops(df)
    plot_latency(df)


if __name__ == "__main__":
    main(sys.argv[1:])
