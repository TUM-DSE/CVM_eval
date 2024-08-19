#!/usr/bin/env python3

from pathlib import Path

from invoke import task

import config
import sqlite3
import pandas as pd

COLUMNS = {
    "date": "TIMESTAMP",
    "name": "VARCHAR(50)",
    "mpstat_guest": "INTEGER REFERENCES mpstat(id)",
    "mpstat_host": "INTEGER REFERENCES mpstat(id)",
    "vmexits": "INTEGER",
    "dTLB_load_misses": "INTEGER",
    "iTLB_load_misses": "INTEGER",
    "cache_misses": "INTEGER",
    "branch_misses": "INTEGER",
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
