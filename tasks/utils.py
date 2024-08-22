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
    "mpstat": "INTEGER REFERENCES mpstat(id)",
    "perf": "INTEGER REFERENCES perf(id)",
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
    cursor = connection.cursor()
    columns = ", ".join(values.keys())
    formatted_values = []
    for value in values.values():
        if isinstance(value, str):
            formatted_values.append(f"'{value}'")
        else:
            formatted_values.append(str(value))
    values = ", ".join(formatted_values)
    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})")
    connection.commit()
    id = cursor.lastrowid
    cursor.close()
    return id


def query_db(query: str):
    """Query the database with a given query and return a pandas DataFrame."""
    connection = connect_to_db()
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df


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
    return id


def parse_perf(hout, gout):
    """Parse perf output and return dict of metrics"""
    pattern = r"^\s*([\d,]+)\s+([\w-]+)"
    matches = re.findall(
        pattern,
        hout.decode().replace("kvm:kvm_exit", "vmexits"),
        re.MULTILINE,
    )
    host_metrics = {
        metric.replace("-", "_"): count.replace(",", "") for count, metric in matches
    }
    matches = re.findall(pattern, gout.decode(), re.MULTILINE)
    guest_metrics = {
        metric.replace("-", "_"): count.replace(",", "") for count, metric in matches
    }
    connection = connect_to_db()
    ensure_db(connection, table="perf_guest", columns=PERF_COLS)
    ensure_db(connection, table="perf_host", columns=PERF_COLS)
    g_id = insert_into_db(connection, "perf_guest", guest_metrics)
    return insert_into_db(connection, "perf_host", host_metrics)


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
    print("Metrics stopped")

    # parse and save results
    mpstat_id = parse_mpstat(mpstat_hout, mpstat_gout)
    perf_id = parse_perf(perf_hout, perf_gout)
    return mpstat_id, perf_id
