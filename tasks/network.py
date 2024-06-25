import subprocess
from datetime import datetime
from pathlib import Path
import subprocess
import time
import re

from config import PROJECT_ROOT, VM_IP, VM_REMOTE_IP
from qemu import QemuVm

import mysql.connector

COLUMNS = {
    "date": "TIMESTAMP PRIMARY KEY",
    "type": "VARCHAR(10)",
    "size": "VARCHAR(10)",
    "remote": "BOOLEAN",
    "vhost": "BOOLEAN",
    "tls": "BOOLEAN",
}


def connect_to_mysql():
    """Connect to the MySQL server."""
    return mysql.connector.connect(
        host="127.0.0.1",
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


def run_ping(name: str, vm: QemuVm, remote: bool = False):
    """Ping the VM.
    The results are saved in the database 'bench' in table 'ping'.
    """
    vhost = "vhost" in name
    remote = "remote" in name
    attrs = name.split("-")
    ty = attrs[0]
    size = attrs[2]
    columns = COLUMNS.copy()
    ping_columns = {
        "pkt_size": "INT",
        "min": "FLOAT",
        "avg": "FLOAT",
        "max": "FLOAT",
        "mdev": "FLOAT",
    }
    columns.update(ping_columns)
    connection = connect_to_mysql()
    ensure_db(connection, table="ping", columns=columns)

    host_ip = VM_REMOTE_IP if remote else VM_IP
    for pkt_size in [64, 128, 256, 512, 1024]:
        cmd = ["ping", "-c", "30", "-i0.1", "-s", f"{pkt_size}", host_ip]
        output = (
            remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
        )
        pattern = re.compile(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms"
        )
        match = pattern.search(output)
        if match:
            min_rtt, avg_rtt, max_rtt, mdev_rtt = match.groups()
            min_rtt, avg_rtt, max_rtt, mdev_rtt = map(
                float, [min_rtt, avg_rtt, max_rtt, mdev_rtt]
            )
            print(f"Min: {min_rtt}, Avg: {avg_rtt}, Max: {max_rtt}, Mdev: {mdev_rtt}")
            insert_into_db(
                connection,
                "ping",
                {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": f"{ty}",
                    "size": size,
                    "remote": remote,
                    "vhost": vhost,
                    "tls": False,
                    "pkt_size": pkt_size,
                    "min": min_rtt,
                    "avg": avg_rtt,
                    "max": max_rtt,
                    "mdev": mdev_rtt,
                },
            )
        else:
            print("No match")
    connection.close()
    print(f"Results saved to database 'bench' in table 'ping'")


def run_iperf(
    name: str,
    vm: QemuVm,
    udp: bool = False,
    port: int = 7175,
    parallel: int = 8,  # number of parallel streams
    remote: bool = False,
):
    """Run the iperf benchmark on the VM.
    The results are saved in ./bench-result/networking/iperf/{name}/{proto}/{date}/
    """
    if udp:
        proto = "udp"
        pkt_sizes = [64, 128, 256, 512, 1024, 1460]
    else:
        pkt_sizes = [64, 128, 256, 512, 1024, "32K", "128K"]
        proto = "tcp"

    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/iperf/{name}/{proto}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    # start server
    server_cmd = ["iperf", "-s", "-p", f"{port}", "-D"]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)

    # run client
    for pkt_size in pkt_sizes:
        cmd = [
            "iperf",
            "-c",
            f"{VM_REMOTE_IP if remote else VM_IP}",
            "-p",
            f"{port}",
            "-b",
            "0",
            "-i",
            "1",
            "-l",
            f"{pkt_size}",
            "-P",
            f"{parallel}",
        ]
        if udp:
            cmd.append("-u")
        print(cmd)
        output = (
            remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
        )

        lines = output.split("\n")
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_memtier(
    name: str,
    vm: QemuVm,
    server: str = "redis",
    port: int = 6379,
    tls_port: int = 6380,
    tls: bool = True,
    remote: bool = False,
    server_threads: int = 8,
    client_threads: int = 8,
    client_key: str = PROJECT_ROOT / "benchmarks/network/tls/pki/private/client.key",
    client_cert: str = PROJECT_ROOT / "benchmarks/network/tls/pki/issued/client.crt",
    ca_cert: str = PROJECT_ROOT / "benchmarks/network/tls/pki/ca.crt",
):
    """Run the memtier benchmark on the VM using redis or memcached.
    `server_threads` is only valid for memcached.
    The results are saved in ./bench-result/networking/memtier/{server}[-tls]/{name}/{date}/
    """
    if tls:
        tls_ = "-tls"
    else:
        tls_ = ""
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/memtier/{server}{tls_}/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    if server == "redis":
        proto = "redis"
    elif server == "memcached":
        proto = "memcache_binary"
    else:
        raise ValueError(f"Unknown server: {server}")

    server_cmd = [
        "nix-shell",
        "/share/benchmarks/network/shell.nix",
        "--run",
        f"just STANDARD_MEMTIER_PORT={port} TLS_MEMTIER_PORT={tls_port} THREADS={server_threads} run-{server}{tls_}",
    ]
    vm.ssh_cmd(server_cmd)
    print("Server started")
    time.sleep(1)

    host_ip = VM_REMOTE_IP if remote else VM_IP
    bench_path = ("CVM_eval/" if remote else "") + "benchmarks/network/"
    just_cmd = (
        f"just STANDARD_MEMTIER_PORT={port} TLS_MEMTIER_PORT={tls_port} VM_IP={host_ip} PROTOCOL={proto} run-memtier"
        + ("-tls" if tls else "")
    )
    cmd = (
        ["cd", bench_path, "&&", "nix-shell --run", f"'{just_cmd}'"]
        if remote
        else ["nix-shell", f"{bench_path}/shell.nix", "--run", f"{just_cmd}"]
    )
    print(cmd)
    output = remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
    lines = output.split("\n")
    with open(outputdir_host / f"memtier.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_nginx(name: str, vm: QemuVm, remote: bool = False):
    """Run the nginx on the VM and the wrk benchmark on the host.
    The results are saved in ./bench-result/networking/nginx/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/nginx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    nix_shell_path = "benchmarks/network/shell.nix"
    bench_path = "CVM_eval/benchmarks/network/"

    server_cmd = ["nix-shell", f"/share/{nix_shell_path}", "--run", "just run-nginx"]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)

    host_ip = VM_REMOTE_IP if remote else VM_IP
    just_cmd = f"just VM_IP={host_ip} run-wrk"
    just_cmd_ssl = just_cmd + "-ssl"

    # HTTP
    cmd = (
        ["cd", f"{bench_path}", "&&", "nix-shell --run", f"'{just_cmd}'"]
        if remote
        else ["nix-shell", f"{nix_shell_path}", "--run", f"{just_cmd}"]
    )
    print(cmd)
    output = remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
    lines = output.split("\n")
    with open(outputdir_host / f"http.log", "w") as f:
        f.write("\n".join(lines))

    # HTTPS
    cmd = (
        ["cd", f"{bench_path}", "&&", "nix-shell --run", f"'{just_cmd_ssl}'"]
        if remote
        else ["nix-shell", f"{nix_shell_path}", "--run", f"{just_cmd_ssl}"]
    )
    print(cmd)
    output = remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
    lines = output.split("\n")
    with open(outputdir_host / f"https.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def remote_ssh_cmd(command: list[str]):
    """Execute a command with ssh on a remote machine."""
    ssh_command = [
        "ssh",
        "-F",
        "/scratch/luca/CVM_eval/benchmarks/network/ssh_conf",
        "graham.tum",
    ] + command
    return subprocess.check_output(ssh_command).decode()
