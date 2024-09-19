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
    MEMTIER_COLS,
    MPSTAT_COLS,
    NGINX_COLS,
    PING_COLS,
    connect_to_db,
    ensure_db,
    insert_into_db,
    capture_metrics,
)


def run_ping(name: str, vm: QemuVm, pin_base=20, metrics: bool = True):
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
        cmd = f"ping -c 100 -i0.1 -s {pkt_size} {VM_IP}".split(" ")
        if "remote" not in name:
            cmd = ["taskset", "-c", f"{pin_base}"] + cmd
        print(cmd)
        process = (
            remote_ssh_cmd(cmd)
            if "remote" in name
            else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        )
        # Capture metrics for host and guest
        mpstat_ids, perf_ids, bpf_id = (
            capture_metrics(name, 1) if metrics else ((None, None), (None, None), None)
        )
        # pattern matching
        pattern = re.compile(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms"
        )
        out, err = process.communicate()
        if process.returncode != 0:
            print(f"Error running ping: {err.decode()}")
        match = pattern.search(out.decode())
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
                    "mpstat_host": mpstat_ids[0],
                    "mpstat_guest": mpstat_ids[1],
                    "perf_host": perf_ids[0],
                    "perf_guest": perf_ids[1],
                    "bpf": bpf_id,
                },
            )
        else:
            print("No match, stdout: " + out.decode() + "stderr: " + err.decode())
            break
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write(out.decode())
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
    metrics: bool = True,
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
        pkt_sizes = ["128K"]
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
            "-t",
            "30",
            "-P",
            f"{parallel}",
        ]
        if udp:
            cmd.append("-u")
        if "remote" not in name:
            cmd = ["taskset", "-c", f"{pin_start}-{pin_end}"] + cmd
        print(cmd)
        bench_res = (
            remote_ssh_cmd(cmd)
            if "remote" in name
            else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        )
        time.sleep(10)
        # Capture metrics for host and guest
        mpstat_ids, perf_ids, bpf_id = (
            capture_metrics(name, 10, f"{pin_start}-{pin_end}")
            if metrics
            else ((None, None), (None, None), None)
        )
        out, err = bench_res.communicate()
        if bench_res.returncode != 0:
            print(f"Error running iperf: {err.decode()}")
        last_line = re.sub(
            r"\s+", " ", out.decode().strip().split("\n")[-3]
        )  # only search relevant line
        tcp_pattern = r"\[SUM\] .* sec (\d+\.\d+|\d+) (GBytes|MBytes) (\d+\.\d+|\d+) (Gbits/sec|Mbits/sec) .*receiver"
        udp_pattern = r"\[SUM\] .* sec (\d+\.\d+|\d+) (GBytes|MBytes) (\d+\.\d+|\d+) (Gbits/sec|Mbits/sec) .*\s+(\d+)/(\d+) .*receiver"
        pattern = udp_pattern if udp else tcp_pattern
        match = re.search(pattern, last_line, re.DOTALL)
        if match:
            if udp:
                transfer, tunit, bitrate, bunit, lost, total = match.groups()
                lost, total = map(int, [lost, total])
            else:
                transfer, tunit, bitrate, bunit = match.groups()
                lost = total = None
            transfer, bitrate = map(float, [transfer, bitrate])
            transfer = transfer if tunit == "GBytes" else transfer / 1000  # in GBytes
            bitrate = (
                bitrate if bunit == "Gbits/sec" else bitrate / 1000
            )  # in Gbits/sec
            print(f"Transfer: {transfer} GBytes, Bitrate: {bitrate} Gbits/sec")
            insert_into_db(
                connection,
                "iperf",
                {
                    "date": date,
                    "name": name,
                    "mpstat_host": mpstat_ids[0],
                    "mpstat_guest": mpstat_ids[1],
                    "perf_host": perf_ids[0],
                    "perf_guest": perf_ids[1],
                    "streams": parallel,
                    "pkt_size": pkt_size,
                    "bitrate": bitrate,  # in Gbits/sec
                    "transfer": transfer,  # in GBytes
                    "proto": proto,
                    "lost": lost,
                    "total": total,
                    "bpf": bpf_id,
                },
            )
        else:
            print("No match, stdout: " + out.decode() + "stderr: " + err.decode())
            break
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write(out.decode())
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
    metrics: bool = False,
):
    """Run the memtier benchmark on the VM using redis or memcached.
    `server_threads` is only valid for memcached.
    The results are saved in ./bench-result/network/memtier/{server}[-tls]/{name}/{date}/ and in the memtier table of the database.
    """
    if tls:
        tls_ = "-tls"
    else:
        tls_ = ""
    date = datetime.now().strftime(DATE_FORMAT)
    # File setup
    outputdir = Path(f"./bench-result/network/memtier/{server}{tls_}/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    # Database setup
    connection = connect_to_db()
    ensure_db(connection, table="memtier", columns=MEMTIER_COLS)

    # Benchmark
    if server == "redis":
        proto = "redis"
    elif server == "memcached_t":
        proto = "memcache_text"
        server = "memcached"
    elif server == "memcached_b":
        proto = "memcache_binary"
        server = "memcached"
    else:
        raise ValueError(f"Unknown server: {server}")

    if server_threads is None:
        if "resource" in vm.config:
            server_threads = vm.config["resource"].cpu
        else:
            server_threads = 1

    if client_threads is None:
        client_threads = server_threads

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
            "memtier_benchmark",
            "-h",
            f"{VM_IP}",
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
            "--test-time=30",
        ]
    else:
        cmd = [
            "memtier_benchmark",
            "-h",
            f"{VM_IP}",
            "-p",
            f"{port}",
            "-t",
            f"{client_threads}",
            "-c",
            "100",
            "--pipeline=40",
            f"--protocol={proto}",
            "--test-time=30",
        ]
    if "remote" not in name:
        cmd = ["taskset", "-c", f"{pin_start}-{pin_end}"] + cmd
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # Capture metrics for host and guest
    mpstat_ids, perf_ids, bpf_id = (
        capture_metrics(name, 10, f"{pin_start}-{pin_end}")
        if metrics
        else ((None, None), (None, None), None)
    )
    out, err = bench_res.communicate()
    if bench_res.returncode != 0:
        print(f"Error running memtier: Stderr: {err.decode()}, Stdout: {out.decode()}")

    pattern = r"(\d+)\s+Threads.*?Totals\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)\s+(\d+\.\d+)"
    match = re.search(pattern, out.decode(), re.DOTALL)
    if match:
        threads, ops_per_sec, hits, misses, lat_avg, lat_max, transfer_rate = map(
            float, match.groups()
        )
        print(
            f"Threads: {threads}, Latency: {lat_avg}ms, Max: {lat_max}ms, Ops/s: {ops_per_sec}, Transfer rate: {transfer_rate}KB/s"
        )
        insert_into_db(
            connection,
            "memtier",
            {
                "date": date,
                "name": name,
                "mpstat_host": mpstat_ids[0],
                "mpstat_guest": mpstat_ids[1],
                "perf_host": perf_ids[0],
                "perf_guest": perf_ids[1],
                "tls": tls,
                "hits_per_sec": hits,
                "misses_per_sec": misses,
                "lat_max": lat_max,
                "lat_avg": lat_avg,
                "ops_per_sec": ops_per_sec,
                "transfer_rate": transfer_rate,
                "server": server,
                "proto": proto,
                "client_threads": threads,
                "server_threads": server_threads,
                "bpf": bpf_id,
            },
        )

    else:
        print("No match")

    with open(outputdir_host / f"memtier.log", "w") as f:
        f.write(out.decode())

    print(f"Results saved in {outputdir_host} and in the database")


def run_nginx(
    name: str,
    vm: QemuVm,
    threads: int = 8,
    connections: int = 300,
    duration: str = "30s",
    pin_start: int = 20,
    pin_end: Optional[int] = None,
    metrics: bool = False,
):
    """Run the nginx on the VM and the wrk benchmark on the host.
    The results are saved in ./bench-result/network/nginx/{name}/{date}/ and in the nginx table of the database.
    """
    date = datetime.now().strftime(DATE_FORMAT)
    # File setup
    outputdir = Path(f"./bench-result/network/nginx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    # Database setup
    connection = connect_to_db()
    ensure_db(connection, table="nginx", columns=NGINX_COLS)
    # Benchmark
    if pin_end is None:
        pin_end = pin_start + threads - 1

    server_cmd = ["just", "-f", "/share/benchmarks/network/justfile", "run-nginx"]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)

    # HTTP
    cmd = [
        "wrk",
        f"http://{VM_IP}",
        f"-t{threads}",
        f"-c{connections}",
        f"-d{duration}",
    ]
    if "remote" not in name:
        cmd = ["taskset", "-c", f"{pin_start}-{pin_end}"] + cmd
    print(cmd)
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # capture metrics for host and guest
    mpstat_ids, perf_ids, bpf_id = (
        capture_metrics(name, 10, f"{pin_start}-{pin_end}")
        if metrics
        else ((None, None), (None, None), None)
    )
    out, err = bench_res.communicate()
    if bench_res.returncode != 0:
        print(f"Error running wrk: {err.decode()}")
    with open(outputdir_host / f"http.log", "w") as f:
        f.write(out.decode())
    pattern = r"Latency\s+(\d+\.\d+).?s\s+(\d+\.\d+).s\s+(\d+\.\d+).?s.*?Requests/sec:\s+(\d+\.\d+).*?Transfer/sec:\s+(\d+\.\d+).?B"
    match = re.search(pattern, out.decode(), re.DOTALL)
    if match:
        lat_avg, lat_stdev, lat_max, req_per_sec, transfer_rate = map(
            float, match.groups()
        )
        print(
            f"HTTP Latency: {lat_avg}ms, Max: {lat_max}ms, Req/s: {req_per_sec}, Transfer rate: {transfer_rate}KB/s"
        )
        insert_into_db(
            connection,
            "nginx",
            {
                "date": date,
                "name": name,
                "tls": False,
                "lat_max": lat_max,
                "lat_stdev": lat_stdev,
                "lat_avg": lat_avg,
                "req_per_sec": req_per_sec,
                "transfer_rate": transfer_rate,
                "mpstat_host": mpstat_ids[0],
                "mpstat_guest": mpstat_ids[1],
                "perf_host": perf_ids[0],
                "perf_guest": perf_ids[1],
                "bpf": bpf_id,
            },
        )
    else:
        print("HTTP no match")
    time.sleep(1)
    # HTTPS
    cmd = [
        "wrk",
        f"https://{VM_IP}",
        f"-t{threads}",
        f"-c{connections}",
        f"-d{duration}",
    ]
    if "remote" not in name:
        cmd = ["taskset", "-c", f"{pin_start}-{pin_end}"] + cmd
    print(cmd)
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # capture metrics for host and guest
    mpstat_ids, perf_ids, bpf_id = (
        capture_metrics(name, 10, f"{pin_start}-{pin_end}")
        if metrics
        else ((None, None), (None, None), None)
    )
    out, err = bench_res.communicate()
    if bench_res.returncode != 0:
        print(f"Error running wrk: {err.decode()}")
    with open(outputdir_host / f"https.log", "w") as f:
        f.write(out.decode())
    match = re.search(pattern, out.decode(), re.DOTALL)
    if match:
        lat_avg, lat_stdev, lat_max, req_per_sec, transfer_rate = map(
            float, match.groups()
        )
        print(
            f"HTTPS Latency: {lat_avg}ms, Max: {lat_max}ms, Req/s: {req_per_sec}, Transfer rate: {transfer_rate}KB/s"
        )
        insert_into_db(
            connection,
            "nginx",
            {
                "date": date,
                "name": name,
                "tls": True,
                "lat_max": lat_max,
                "lat_stdev": lat_stdev,
                "lat_avg": lat_avg,
                "req_per_sec": req_per_sec,
                "transfer_rate": transfer_rate,
                "mpstat_host": mpstat_ids[0],
                "mpstat_guest": mpstat_ids[1],
                "perf_host": perf_ids[0],
                "perf_guest": perf_ids[1],
                "bpf": bpf_id,
            },
        )
    else:
        print("HTTPS no match")
    print(f"Results saved in {outputdir_host} and in the database")


def remote_ssh_cmd(command: list[str]):
    """Execute a command with ssh on a remote machine."""
    ssh_command = [
        "ssh",
        "-F",
        f"{SSH_CONF_PATH}",
        "river.tum",
    ] + command
    return subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
