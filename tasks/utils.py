#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess

from invoke import task

import config
import sqlite3
import pandas as pd

COLUMNS = {
    "date": "TIMESTAMP",
    "name": "VARCHAR(50)",
    "mpstat_guest": "INTEGER REFERENCES mpstat(id)",
    "mpstat_host": "INTEGER REFERENCES mpstat(id)",
    "perf_guest": "INTEGER REFERENCES perf(id)",
    "perf_host": "INTEGER REFERENCES perf(id)",
    "bpf": "INTEGER REFERENCES bpf(id)",
}

MPSTAT_COLS = {
    "id": "INTEGER PRIMARY KEY",
    "usr": "FLOAT",
    "nice": "FLOAT",
    "sys": "FLOAT",
    "iowait": "FLOAT",
    "irq": "FLOAT",
    "soft": "FLOAT",
    "steal": "FLOAT",
    "guest": "FLOAT",
    "gnice": "FLOAT",
    "idle": "FLOAT",
}

PERF_COLS = {
    "id": "INTEGER PRIMARY KEY",
    "vmexits": "INTEGER",
    "dTLB_load_misses": "INTEGER",
    "iTLB_load_misses": "INTEGER",
    "cache_misses": "INTEGER",
    "branch_misses": "INTEGER",
    "instructions": "INTEGER",
    "cycles": "INTEGER",
    "L1_misses": "INTEGER",
    "L2_misses": "INTEGER",
}

BPF_COLS = {
    "id": "INTEGER PRIMARY KEY",
    "duration": "FLOAT",
}

PING_COLS = {
    **COLUMNS,
    "pkt_size": "INT",
    "min": "FLOAT",
    "avg": "FLOAT",
    "max": "FLOAT",
    "mdev": "FLOAT",
    "PRIMARY KEY": "(date, pkt_size)",
}

IPERF_COLS = {
    **COLUMNS,
    "streams": "INT",
    "pkt_size": "VARCHAR(6)",
    "bitrate": "FLOAT",
    "transfer": "FLOAT",
    "proto": "VARCHAR(3)",
    "lost": "INT",
    "total": "INT",
    "PRIMARY KEY": "(date, pkt_size)",
}

MEMTIER_COLS = {
    **COLUMNS,
    "tls": "BOOLEAN",
    "hits_per_sec": "FLOAT",
    "misses_per_sec": "FLOAT",
    "lat_max": "FLOAT",
    "lat_avg": "FLOAT",
    "ops_per_sec": "FLOAT",
    "transfer_rate": "FLOAT",  # in KB/s
    "server": "VARCHAR(10)",
    "proto": "VARCHAR(20)",
    "client_threads": "INT",
    "server_threads": "INT",
    "PRIMARY KEY": "(date)",
}

NGINX_COLS = {
    **COLUMNS,
    "tls": "BOOLEAN",
    "lat_max": "FLOAT",
    "lat_avg": "FLOAT",
    "lat_stdev": "FLOAT",
    "req_per_sec": "FLOAT",  # in Requests/s
    "transfer_rate": "FLOAT",  # in KB/s
    "PRIMARY KEY": "(date, tls)",
}

TENSORFLOW_COLS = {
    **COLUMNS,
    "thread_cnt": "INT",
    "examples_per_sec": "FLOAT",
    "PRIMARY KEY": "(date)",
}

NPB_COLS = {
    **COLUMNS,
    "prog": "VARCHAR(2)",
    "size": "VARCHAR(1)",
    "policy": "VARCHAR(10)",
    "threads": "INT",
    "time": "FLOAT",  # in seconds
    "mops": "FLOAT",
    "PRIMARY KEY": "(date, policy)",
}


@task
def show_config(ctx):
    """Show script configuration"""
    print(f"SCRIPT_ROOT: {config.SCRIPT_ROOT}")
    print(f"PROJECT_ROOT: {config.PROJECT_ROOT}")
    print(f"BUILD_DIR: {config.BUILD_DIR}")


@task
def clear_db(ctx, table: str = "test_table"):
    """Clear the database."""
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    connection.commit()
    cursor.close()


def connect_to_db():
    """Connect to sqlite."""
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    if not Path(config.DB_PATH).exists():
        Path(config.DB_PATH).touch()
    return sqlite3.connect(config.DB_PATH)


def ensure_db(connection, table: str = "test_table", columns: dict = {}):
    """Ensure the database exists."""
    cursor = connection.cursor()
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {table} ({', '.join([f'{name} {type}' for name, type in columns.items()])})"
    )
    connection.commit()
    cursor.close()


def insert_into_db(connection, table: str, values: dict):
    """Insert values into the database."""
    add_cols_to_db(connection, table, values)
    cursor = connection.cursor()
    columns = ", ".join(values.keys())
    formatted_values = []
    for value in values.values():
        if value is None:
            formatted_values.append("NULL")
        elif isinstance(value, str):
            formatted_values.append(f"'{value}'")
        else:
            formatted_values.append(str(value))
    values = ", ".join(formatted_values)
    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})")
    connection.commit()
    id = cursor.lastrowid
    cursor.close()
    return id


def add_cols_to_db(connection, table: str, columns: dict):
    """Add columns to the database."""
    cursor = connection.cursor()
    for name, value in columns.items():
        if not column_exists(cursor, table, name):
            if type(value) is int:
                sql_type = "INTEGER"
            elif type(value) is float:
                sql_type = "FLOAT"
            else:
                sql_type = "VARCHAR(50)"
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
    connection.commit()
    cursor.close()


def column_exists(cursor, table, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def query_db(query: str):
    """Query the database with a given query and return a pandas DataFrame."""
    connection = connect_to_db()
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df


@task
def write_db(ctx, query: str):
    """Write to the database with a given query."""
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def parse_mpstat(hout, gout):
    """Parse mpstat output and save to database"""
    all_pattern = r"Average:\s+all\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
    single_pattern = r"Average:\s+\d+\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
    connection = connect_to_db()
    ensure_db(connection, table="mpstat_guest", columns=MPSTAT_COLS)
    ensure_db(connection, table="mpstat_host", columns=MPSTAT_COLS)
    id = 0
    # Parse and save results
    gmatch = re.search(all_pattern, gout.decode())
    if not gmatch:
        print("No match in guest output: " + gout.decode())
        return
    gvals = [float(val) for val in gmatch.groups()]
    hmatch = re.search(all_pattern, hout.decode())
    hvals = [0] * 10
    if not hmatch:
        hmatches = re.findall(single_pattern, hout.decode(), re.MULTILINE)
        if not hmatches:
            print("No match in host output: " + hout.decode())
            return
        for match in hmatches:
            for i in range(10):
                hvals[i] += float(match[i])
        for i in range(10):
            hvals[i] /= len(hmatches)
    ids = []
    for vals in [hvals, gvals]:
        usr, nice, sys, iowait, irq, soft, steal, guest, gnice, idle = vals
        id = insert_into_db(
            connection,
            f"mpstat_{'guest' if vals == gvals else 'host'}",
            {
                "usr": usr,
                "nice": nice,
                "sys": sys,
                "iowait": iowait,
                "irq": irq,
                "soft": soft,
                "steal": steal,
                "guest": guest,
                "gnice": gnice,
                "idle": idle,
            },
        )
        ids.append(id),
    return ids


def parse_perf(hout, gout):
    """Parse perf output and return dict of metrics"""
    pattern = r"^\s*([\d,]+)\s+([\w-]+)"
    matches = re.findall(
        pattern,
        hout.decode()
        .replace("kvm:kvm_exit", "vmexits")
        .replace("L1-dcache-load-misses", "L1_misses")
        .replace("l2_cache_req_stat.ic_dc_miss_in_l2", "L2_misses"),
        re.MULTILINE,
    )
    host_metrics = {
        metric.replace("-", "_"): count.replace(",", "") for count, metric in matches
    }
    matches = re.findall(
        pattern,
        gout.decode()
        .replace("L1-dcache-load-misses", "L1_misses")
        .replace("l2_cache_req_stat.ic_dc_miss_in_l2", "L2_misses"),
        re.MULTILINE,
    )
    guest_metrics = {
        metric.replace("-", "_"): count.replace(",", "") for count, metric in matches
    }
    connection = connect_to_db()
    ensure_db(connection, table="perf_guest", columns=PERF_COLS)
    ensure_db(connection, table="perf_host", columns=PERF_COLS)
    g_id = insert_into_db(connection, "perf_guest", guest_metrics)
    h_id = insert_into_db(connection, "perf_host", host_metrics)
    return h_id, g_id


def parse_bpf(output, duration):
    """Parse BPF output and write to database"""
    pattern = r"^\s*([\w_]+):\s*(\d+)"
    matches = re.findall(pattern, output.decode(), re.MULTILINE)
    metrics = {name: count for name, count in matches}
    metrics["duration"] = duration
    connection = connect_to_db()
    ensure_db(connection, table="bpf", columns=BPF_COLS)
    id = insert_into_db(connection, "bpf", metrics)
    return id


def capture_metrics(name: str, duration: int = 5, range: str = "ALL"):
    """Capture some metrics and save results to the database."""
    # mpstat
    mpstat_host = subprocess.Popen(
        ["just", "mpstat-host", name, str(duration), range],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    mpstat_guest = subprocess.Popen(
        ["just", "mpstat-guest", name, str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # perf
    perf_host = subprocess.Popen(
        ["just", "perf-host", name, str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    perf_guest = subprocess.Popen(
        ["just", "perf-guest", name, str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # bpf
    bpf = subprocess.Popen(
        ["just", "bpf", str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("Metrics started")

    # mpstat
    mpstat_hout, herr = mpstat_host.communicate()
    if mpstat_host.returncode != 0:
        print(f"Error running mpstat: {herr.decode()}")
    mpstat_gout, gerr = mpstat_guest.communicate()
    if mpstat_guest.returncode != 0:
        print(f"Error running mpstat: {gerr.decode()}")

    # perf
    perf_hout, herr = perf_host.communicate()
    if perf_host.returncode != 0:
        print(f"Error running perf: {herr.decode()}")
    perf_gout, gerr = perf_guest.communicate()
    if perf_guest.returncode != 0:
        print(f"Error running perf: {gerr.decode()}")
    bpf_out, berr = bpf.communicate()
    print("Metrics stopped")

    # parse and save results
    mpstat_ids = parse_mpstat(mpstat_hout, mpstat_gout)
    perf_ids = parse_perf(perf_hout, perf_gout)
    bpf_id = parse_bpf(bpf_out, duration)
    return mpstat_ids, perf_ids, bpf_id


def determine_size(row):
    if "small" in row["name"]:
        return "small"
    elif "medium" in row["name"]:
        return "medium"
    elif "large" in row["name"]:
        return "large"
    else:
        return "xlarge"
