import re
import subprocess
from datetime import datetime
from pathlib import Path
import subprocess
import time
from typing import Optional

from config import PROJECT_ROOT, VM_IP, DATE_FORMAT, SSH_CONF_PATH
from qemu import QemuVm
from utils import (
    IPERF_COLS,
    MPSTAT_COLS,
    connect_to_db,
    ensure_db,
    insert_into_db,
    PING_COLS,
)

JUSTFILE_VM = PROJECT_ROOT / "benchmarks/network/justfile"


def run_ping(name: str, vm: QemuVm, pin_base=20):
    """Ping the VM.
    The results are saved in ./bench-results/network/ping/{name}/{date}
    And in the ping table of the database.
    """
    # File setup
    date = datetime.now().strftime(DATE_FORMAT)
    outputdir = Path(f"./bench-result/network/ping/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    # Database setup
    connection = connect_to_db()
    ensure_db(connection, table="ping", columns=PING_COLS)
    # Benchmark
    for pkt_size in [64, 128, 256, 512, 1024]:
        cmd = f"taskset -c {pin_base} ping -c 30 -i0.1 -s {pkt_size} {VM_IP}".split(" ")
        print(cmd)
        try:
            result = (
                remote_ssh_cmd(cmd)
                if "remote" in name
                else subprocess.run(cmd, capture_output=True, text=True)
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running ping: {result.stderr}")
            break
        # pattern matching
        pattern = re.compile(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms"
        )
        match = pattern.search(result.stdout)
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
                    "date": date,
                    "name": name,
                    "pkt_size": pkt_size,
                    "min": min_rtt,
                    "avg": avg_rtt,
                    "max": max_rtt,
                    "mdev": mdev_rtt,
                },
            )
        else:
            print("No match, stdout: " + result.stdout + "stderr: " + result.stderr)
            break
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write(result.stdout)
    connection.close()
    print(f"Results saved in {outputdir_host} and in the database")


def run_iperf(
    name: str,
    vm: QemuVm,
    udp: bool = False,
    port: int = 7175,
    parallel: Optional[int] = None,
    pin_start: int = 20,
    pin_end: Optional[int] = None,
):
    """Run the iperf benchmark on the VM.
    The results are saved in ./bench-result/network/iperf/{name}/{proto}/{date}/
    and in the iperf table of the database.
    """
    if udp:
        proto = "udp"
        pkt_sizes = [64, 128, 256, 512, 1024, 1460]
        if parallel is None:
            parallel = 8
    else:
        pkt_sizes = [64, 128, 256, 512, 1024, "32K", "128K"]
        proto = "tcp"
        if parallel is None:
            parallel = 32
    if pin_end is None:
        pin_end = pin_start + parallel - 1

    # File setup
    date = datetime.now().strftime(DATE_FORMAT)
    outputdir = Path(f"./bench-result/network/iperf/{name}/{proto}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    # Database setup
    connection = connect_to_db()
    ensure_db(connection, table="iperf", columns=IPERF_COLS)
    # start server
    server_cmd = [
        "taskset",
        "-c",
        f"0-{pin_start-1}",
        "iperf",
        "-s",
        "-p",
        f"{port}",
        "-D",
    ]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)
    # run client
    for pkt_size in pkt_sizes:
        cmd = [
            "taskset",
            "-c",
            f"{pin_start}-{pin_end}",
            "iperf",
            "-c",
            f"{VM_IP}",
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
        # Capture metrics for host and guest
        host, guest = start_metrics(name, 9)
        try:
            bench_res = (
                remote_ssh_cmd(cmd)
                if "remote" in name
                else subprocess.run(cmd, capture_output=True, text=True)
            )
        except subprocess.CalledProcessError as _:
            print(f"Error running iperf: {bench_res.stderr}")
            break
        ids = stop_metrics(host, guest)
        pattern = r"\[SUM\].*sec\s+(\d+\.\d+)\s+.*\s+(\d+\.\d+)\s+.*receiver"
        match = re.search(pattern, bench_res.stdout, re.DOTALL)
        if match:
            bitrate, transfer = map(float, match.groups())
            print(f"Bitrate: {bitrate}, Transfer: {transfer}")
            insert_into_db(
                connection,
                "iperf",
                {
                    "date": date,
                    "name": name,
                    "mpstat_host": ids[0],
                    "mpstat_guest": ids[1],
                    "streams": parallel,
                    "pkt_size": pkt_size,
                    "bitrate": bitrate,  # in Gbits/sec
                    "transfer": transfer,  # in GBytes
                    "proto": proto,
                },
            )
            time.sleep(1)
        else:
            print(
                "No match, stdout: " + bench_res.stdout + "stderr: " + bench_res.stderr
            )
            break
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write(bench_res.stdout)
        # workaround to avoid "iperf3: error - unable to receive control message - port may not be available"
        time.sleep(1)
    print(f"Results saved in {outputdir_host} and in table iperf of the database")


def run_memtier(
    name: str,
    vm: QemuVm,
    server: str = "redis",
    port: int = 6379,
    tls_port: int = 6380,
    tls: bool = False,
    server_threads: Optional[int] = None,
    client_threads: Optional[int] = None,
    client_key: str = PROJECT_ROOT / "benchmarks/network/tls/pki/private/client.key",
    client_cert: str = PROJECT_ROOT / "benchmarks/network/tls/pki/issued/client.crt",
    ca_cert: str = PROJECT_ROOT / "benchmarks/network/tls/pki/ca.crt",
    pin_start: int = 20,
    pin_end: Optional[int] = None,
):
    """Run the memtier benchmark on the VM using redis or memcached.
    `server_threads` is only valid for memcached.
    The results are saved in ./bench-result/network/memtier/{server}[-tls]/{name}/{date}/
    """
    if tls:
        tls_ = "-tls"
    else:
        tls_ = ""
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/network/memtier/{server}{tls_}/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    if server == "redis":
        proto = "redis"
    elif server == "memcached":
        proto = "memcache_binary"
    else:
        raise ValueError(f"Unknown server: {server}")

    if server_threads is None:
        if "resource" in vm.config:
            server_threads = vm.config["resource"].cpu
        else:
            server_threads = 1

    if client_threads is None:
        if server == "redis":
            client_threads = 8
        else:
            client_threads = vm.config["resource"].cpu

    if pin_end is None:
        pin_end = pin_start + client_threads - 1

    server_cmd = [
        "just",
        "-f",
        "/share/benchmarks/network/justfile",
        f"STANDARD_MEMTIER_PORT={port}",
        f"TLS_MEMTIER_PORT={tls_port}",
        f"THREADS={server_threads}",
        f"run-{server}{tls_}",
    ]
    vm.ssh_cmd(server_cmd)
    print("Server started")
    time.sleep(1)

    if tls:
        cmd = [
            "taskset",
            "-c",
            f"{pin_start}-{pin_end}",
            "memtier_benchmark",
            f"--host={VM_IP}",
            "-p",
            f"{tls_port}",
            "-t",
            f"{client_threads}",
            "-c",
            "100",
            "--pipeline=40",
            f"--protocol={proto}",
            "--tls",
            f"--cert={client_cert}",
            f"--key={client_key}",
            f"--cacert={ca_cert}",
        ]
    else:
        cmd = [
            "taskset",
            "-c",
            f"{pin_start}-{pin_end}",
            "memtier_benchmark",
            f"--host={VM_IP}",
            "-p",
            f"{port}",
            "-t",
            f"{client_threads}",
            "-c",
            "100",
            "--pipeline=40",
            f"--protocol={proto}",
        ]
    print(cmd)
    output = subprocess.check_output(cmd).decode()
    lines = output.split("\n")
    with open(outputdir_host / f"memtier.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_nginx(
    name: str,
    vm: QemuVm,
    threads: int = 8,
    connections: int = 300,
    duration: str = "30s",
    pin_start: int = 20,
    pin_end: Optional[int] = None,
):
    """Run the nginx on the VM and the wrk benchmark on the host.
    The results are saved in ./bench-result/network/nginx/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/network/nginx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    if pin_end is None:
        pin_end = pin_start + threads - 1

    server_cmd = ["just", "-f", "/share/benchmarks/network/justfile", "run-nginx"]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)

    # HTTP
    cmd = [
        "taskset",
        "-c",
        f"{pin_start}-{pin_end}",
        "wrk",
        f"http://{VM_IP}",
        f"-t{threads}",
        f"-c{connections}",
        f"-d{duration}",
    ]
    print(cmd)
    output = subprocess.run(cmd, capture_output=True, text=True)
    if output.returncode != 0:
        print(f"Error running wrk: {output.stderr}")
    lines = output.stdout.split("\n")
    with open(outputdir_host / f"http.log", "w") as f:
        f.write("\n".join(lines))

    # HTTPS
    cmd = [
        "taskset",
        "-c",
        f"{pin_start}-{pin_end}",
        "wrk",
        f"https://{VM_IP}",
        f"-t{threads}",
        f"-c{connections}",
        f"-d{duration}",
    ]
    print(cmd)
    output = subprocess.run(cmd, capture_output=True, text=True)
    if output.returncode != 0:
        print(f"Error running wrk: {output.stderr}")
    lines = output.stdout.split("\n")
    with open(outputdir_host / f"https.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def remote_ssh_cmd(command: list[str]):
    """Execute a command with ssh on a remote machine."""
    ssh_command = [
        "ssh",
        "-F",
        f"{SSH_CONF_PATH}",
        "graham.tum",
    ] + command
    return subprocess.run(ssh_command, capture_output=True, text=True)


def start_metrics(name: str, duration: int = 5):
    """Caputre relevant metrics for the given duration."""
    cmd_host = ["just", "mpstat-host", name, str(duration)]
    cmd_guest = ["just", "mpstat-guest", name, str(duration)]
    host = subprocess.Popen(cmd_host, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    guest = subprocess.Popen(cmd_guest, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Metrics started")
    return host, guest


def stop_metrics(host, guest):
    """Stop the metrics capture and save results to the database."""
    host.terminate()
    guest.terminate()
    hout, herr = host.communicate()
    gout, gerr = guest.communicate()
    print("Metrics stopped")
    # parse and save results
    pattern = r"Average:\s+all\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"
    connection = connect_to_db()
    ensure_db(connection, table="mpstat", columns=MPSTAT_COLS)
    ids = []
    # Parse and save results
    for output in [hout, gout]:
        match = re.search(pattern, output.decode())
        if not match:
            print("No match, output: " + output.decode())
            continue
        usr, nice, sys, iowait, irq, soft, steal, guest, gnice, idle = match.groups()
        id = insert_into_db(
            connection,
            "mpstat",
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
        ids.append(id)
    return ids
