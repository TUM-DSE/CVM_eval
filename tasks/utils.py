#!/usr/bin/env python3

from pathlib import Path

from invoke import task

import config
import sqlite3
import pandas as pd


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
    cursor.close()


def query_db(query: str):
    """Query the database with a given query and return a pandas DataFrame."""
    connection = connect_to_db()
    df = pd.read_sql_query(query, connection)
    connection.close()
    return df
