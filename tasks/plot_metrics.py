from utils import query_db


def plot_ipc(sns, ax, x, hue, df, palette):
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


def plot_cpu(sns, ax, x, hue, df, palette):
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


def plot_vmexit(sns, ax, x, hue, df, palette):
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
        y=df["vmexits"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("VM Exits per 1M Instructions")


def plot_dTLB_misses(sns, ax, x, hue, df, palette):
    df = df.merge(
        query_db("SELECT id, dTLB_load_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["dTLB_load_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("dTLB load misses per 1M Instructions")


def plot_iTLB_misses(sns, ax, x, hue, df, palette):
    df = df.merge(
        query_db("SELECT id, iTLB_load_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["iTLB_load_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("iTLB misses per 1M Instructions")


def plot_cache_misses(sns, ax, x, hue, df, palette):
    df = df.merge(
        query_db("SELECT id, cache_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["cache_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("Cache misses per 1M Instructions")


def plot_branch_misses(sns, ax, x, hue, df, palette):
    df = df.merge(
        query_db("SELECT id, branch_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["branch_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("Branch misses per 1M Instructions")


def plot_l2_misses(sns, ax, x, hue, df, palette):
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
        y=df["L2_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("L2 misses per 1M Instructions")


def plot_l1_misses(sns, ax, x, hue, df, palette):
    df = df.merge(
        query_db("SELECT id, L1_misses, instructions FROM perf_guest"),
        left_on="perf_guest",
        right_on="id",
        how="left",
    )
    sns.lineplot(
        data=df,
        x=x,
        y=df["L1_misses"] / (df["instructions"] / 1e6),
        ax=ax,
        palette=palette,
        marker="o",
        hue=hue,
        linestyle="dotted",
        legend=False,
        errorbar=None,
    )
    ax.set_ylabel("L1 misses per 1M Instructions")


METRIC_FUNCS = {
    "vmexits": plot_vmexit,
    "cpu": plot_cpu,
    "ipc": plot_ipc,
    "dTLB_misses": plot_dTLB_misses,
    "iTLB_misses": plot_iTLB_misses,
    "cache_misses": plot_cache_misses,
    "branch_misses": plot_branch_misses,
    "L2_misses": plot_l2_misses,
    "L1_misses": plot_l1_misses,
}
