#!/usr/bin/env python3

from pathlib import Path

from invoke import task

import config
import mysql.connector


@task
def show_config(ctx):
    """Show script configuration"""
    print(f"SCRIPT_ROOT: {config.SCRIPT_ROOT}")
    print(f"PROJECT_ROOT: {config.PROJECT_ROOT}")
    print(f"BUILD_DIR: {config.BUILD_DIR}")


@task
def test_db_connection(ctx):
    """Test the database connection."""
    connection = connect_to_mysql()
    if connection.is_connected():
        print("Connected to MySQL server")
    else:
        print("Failed to connect to MySQL server")


def connect_to_mysql():
    """Connect to the MySQL server."""
    return mysql.connector.connect(
        host=f"{config.DB_IP}",
        user="root",
        password="",
    )


def ensure_db(
    connection, database: str = "bench", table: str = "test_table", columns: dict = {}
):
    """Ensure the database exists."""
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    cursor.execute(f"USE {database}")
    cols = ", ".join([f"{name} {type}" for name, type in columns.items()])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
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
