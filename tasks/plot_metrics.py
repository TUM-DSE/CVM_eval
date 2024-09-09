import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
from typing import Any, Dict, List, Union, Optional
import pandas as pd
from pathlib import Path
from invoke import task
from typing import Optional
from utils import query_db, determine_size


def plot_ipc(sns, ax, x, hue, df, palette, _):
    df = df.merge(
        query_db("SELECT id, instructions, cycles FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["instructions"] / df["cycles"],
        hue=hue,
        ax=ax,
        palette=palette,
        marker="o",
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("Instructions per Cycle")


def plot_cpu(sns, ax, x, hue, df, palette, _):
    df = df.merge(
        query_db("SELECT id ,idle FROM mpstat_guest"),
        left_on="mpstat_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=(100 - df["idle"]),
        ax=ax,
        palette=palette if hue else None,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("CPU Utilization (%)")


def plot_vmexit(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: str = "1M Instructions",
):
    df = df.merge(
        query_db("SELECT id, vmexits FROM perf_host"),
        left_on="perf_host",
        right_on="id",
        how="left",
    )
    df = df.merge(
        query_db("SELECT id, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["vmexits"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("VM Exits " + (f"per {norm_name}" if norm_name else ""))


def plot_iTLB_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df.merge(
        query_db("SELECT id, iTLB_load_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["iTLB_load_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("iTLB Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_dTLB_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df.merge(
        query_db("SELECT id, dTLB_load_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["dTLB_load_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("dTLB Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_cache_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df.merge(
        query_db("SELECT id, cache_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["cache_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("LLC Cache Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_branch_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df.merge(
        query_db("SELECT id, branch_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["branch_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("Branch Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_l2_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df[df["perf_guest"].notnull()]
    df = df.merge(
        query_db("SELECT id, L2_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["L2_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("L2 Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_l1_misses(
    sns,
    ax,
    x,
    hue,
    df,
    palette,
    norm_name: Optional[str] = None,
):
    df = df.merge(
        query_db("SELECT id, L1_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["L1_misses"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("L1 Misses " + (f"per {norm_name}" if norm_name else ""))


def plot_instructions(sns, ax, x, hue, df, palette, norm_name: Optional[str] = None):
    df = df.merge(
        query_db("SELECT id, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["instructions"]
        / (df["norm"] if "norm" in df.columns else df["instructions"] * 1e-6),
        hue=hue,
        ax=ax,
        palette=palette,
        marker="o",
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("Instructions " + (f"per {norm_name}" if norm_name else ""))


METRIC_FUNCS = {
    "vmexits": plot_vmexit,
    "cpu": plot_cpu,
    "ipc": plot_ipc,
    "instructions": plot_instructions,
    "dTLB_misses": plot_dTLB_misses,
    "iTLB_misses": plot_iTLB_misses,
    "cache_misses": plot_cache_misses,
    "branch_misses": plot_branch_misses,
    "L2_misses": plot_l2_misses,
    "L1_misses": plot_l1_misses,
}


@task
def plot_exit_reasons_ua(ctx, remote: bool = False):
    df = query_db("SELECT * FROM bpf")
    df = df.merge(
        query_db(f"SELECT name, bpf FROM npb WHERE prog = 'ua'"),
        left_on="id",
        right_on="bpf",
        how="left",
    )
    df = df.dropna(subset=["name"])
    df["name"] = df.apply(
        lambda row: row["name"]
        .replace("-direct", "")
        .replace("-small", "")
        .replace("-medium", "")
        .replace("-large", "")
        .replace("-numa", ""),
        axis=1,
    )
    df = df.melt(
        id_vars=["id", "bpf", "name", "duration"],
        var_name="Metric",
        value_name="Value",
    )
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)
    df["Value"] = df["Value"] * df["duration"]

    df = df.groupby(["name", "Metric"], as_index=False)["Value"].mean()
    print(df)
    df = (
        df.groupby("name")
        .apply(lambda x: x.nlargest(5, "Value"))
        .reset_index(drop=True)
    )

    fig, ax = plt.subplots()
    barplot = sns.barplot(
        data=df,
        x="name",
        y="Value",
        ax=ax,
        hue="Metric",
        palette=sns.color_palette("hsv", 10),
        edgecolor="black",
        errorbar=None,
    )

    legend = ax.legend()
    legend.set_title("VMexit reason")

    plt.tight_layout()
    plt.savefig(f"plot/exits/ua.pdf", bbox_inches="tight")
