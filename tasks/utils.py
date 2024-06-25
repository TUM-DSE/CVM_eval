#!/usr/bin/env python3

from pathlib import Path

from invoke import task

import config
import sqlite3


@task
def show_config(ctx):
    """Show script configuration"""
    print(f"SCRIPT_ROOT: {config.SCRIPT_ROOT}")
    print(f"PROJECT_ROOT: {config.PROJECT_ROOT}")
    print(f"BUILD_DIR: {config.BUILD_DIR}")


def connect_to_db():
    """Connect to sqlite."""
    return sqlite3.connect(config.DB_PATH)


def ensure_db(
    connection, database: str = "bench", table: str = "test_table", columns: dict = {}
):
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
    cursor.close()
