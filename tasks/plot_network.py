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
import utils
import datetime


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


@task
def plot_iperf_tcp(ctx):
    df = utils.query_db(f"SELECT * FROM iperf WHERE proto='tcp'")
    df["combined"] = df.apply(
        lambda row: f"{row['type'].upper()}"
        + ("_VHOST" if row["vhost"] else "")
        + ("_R" if row["remote"] else ""),
        axis=1,
    )
    fig, ax = plt.subplots()
    sns.barplot(
        data=df,
        x="pkt_size",
        y="bitrate",
        ax=ax,
        hue="combined",
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("Packet size in bytes")
    ax.set_ylabel("Bitrate in Gbits/sec")
    ax.set_title("Bitrate of iperf using TCP")
    plt.tight_layout()
    plt.savefig(f"plot/iperf_tcp.pdf", bbox_inches="tight")


@task
def plot_iperf_udp(ctx):
    df = utils.query_db(f"SELECT * FROM iperf WHERE proto='udp'")
    df["combined"] = df.apply(
        lambda row: f"{row['type']}"
        + ("_vhost" if row["vhost"] else "")
        + ("_remote" if row["remote"] else ""),
        axis=1,
    )
    fig, ax = plt.subplots()
    sns.barplot(
        data=df,
        x="pkt_size",
        y="bitrate",
        ax=ax,
        hue="combined",
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("Packet size in bytes")
    ax.set_ylabel("Bitrate in Gbits/sec")
    ax.set_title("Bitrate of iperf using UDP")
    plt.tight_layout()
    plt.savefig(f"plot/iperf_udp.pdf", bbox_inches="tight")


@task
def plot_memtier(ctx):
    df = utils.query_db(f"SELECT * FROM memtier")
    df["group"] = df.apply(
        lambda row: f"{row['type']}"
        + ("_v" if row["vhost"] else "")
        + ("_r" if row["remote"] else ""),
        axis=1,
    )
    df["Protocol, TLS"] = df.apply(
        lambda row: f"{row['proto'].upper()}" + (", TLS" if row["tls"] == 1 else ""),
        axis=1,
    )
    fig, ax = plt.subplots()
    sns.barplot(
        data=df,
        x="group",
        y="ops_per_sec",
        ax=ax,
        hue="Protocol, TLS",
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("VM Config")
    ax.set_ylabel("Operations/sec")
    plt.tight_layout()
    plt.savefig(f"plot/memtier.pdf", bbox_inches="tight")


@task
def plot_nginx(ctx):
    df = utils.query_db(f"SELECT * FROM nginx")
    df["group"] = df.apply(
        lambda row: f"{row['type']}"
        + ("_v" if row["vhost"] else "")
        + ("_r" if row["remote"] else ""),
        axis=1,
    )
    fig, ax = plt.subplots()
    sns.barplot(
        data=df,
        x="group",
        y="lat_avg",
        ax=ax,
        hue="tls",
        palette=palette,
        edgecolor="black",
    )
    ax.set_xlabel("VM Config")
    ax.set_ylabel("Average latency in ms")
    plt.tight_layout()
    plt.savefig(f"plot/nginx.pdf", bbox_inches="tight")
