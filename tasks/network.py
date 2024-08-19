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
        process = (
            remote_ssh_cmd(cmd)
            if "remote" in name
            else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            "-t",
            "30",
            "-P",
            f"{parallel}",
        ]
        if udp:
            cmd.append("-u")
        print(cmd)
        bench_res = (
            remote_ssh_cmd(cmd)
            if "remote" in name
            else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        )
        time.sleep(10)
        # Capture metrics for host and guest
        ids, counters = capture_metrics(name, 10)
        out, err = bench_res.communicate()
        if bench_res.returncode != 0:
            print(f"Error running iperf: {err.decode()}")
        last_line = re.sub(
            r"\s+", " ", out.decode().strip().split("\n")[-3]
        )  # only search relevant line
        print(last_line)
        pattern = r"\[SUM\] .* sec (\d+\.\d+|\d+) (GBytes|MBytes) (\d+\.\d+|\d+) (Gbits/sec|Mbits/sec) .*receiver"
        match = re.search(pattern, last_line, re.DOTALL)
        if match:
            transfer, tunit, bitrate, bunit = match.groups()
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
                    "mpstat_host": ids[0],
                    "mpstat_guest": ids[1],
                    "streams": parallel,
                    "pkt_size": pkt_size,
                    "bitrate": bitrate,  # in Gbits/sec
                    "transfer": transfer,  # in GBytes
                    "proto": proto,
                    **counters,
                },
            )
        else:
            print("No match, stdout: " + out.decode() + "stderr: " + err.decode())
            print(last_line)
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
            "--test-time=30",
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
            "--test-time=30",
        ]
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # Capture metrics for host and guest
    ids, counters = capture_metrics(name, 10)
    out, err = bench_res.communicate()
    if bench_res.returncode != 0:
        print(f"Error running memtier: {err.decode()}")

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
                "mpstat_host": ids[0],
                "mpstat_guest": ids[1],
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
                **counters,
            },
        )

    else:
        print("No match")

    with open(outputdir_host / f"memtier.log", "w") as f:
        f.write(out.decode())

    print(f"Results saved in {outputdir_host}and in the database")


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
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # capture metrics for host and guest
    ids, counters = capture_metrics(name, 10)
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
                "mpstat_host": ids[0],
                "mpstat_guest": ids[1],
                **counters,
            },
        )
    else:
        print("HTTP no match")
    time.sleep(1)
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
    bench_res = (
        remote_ssh_cmd(cmd)
        if "remote" in name
        else subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    )
    time.sleep(10)
    # capture metrics for host and guest
    ids, counters = capture_metrics(name, 10)
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
                "mpstat_host": ids[0],
                "mpstat_guest": ids[1],
                **counters,
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
        "graham.tum",
    ] + command
    return subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def capture_metrics(name: str, duration: int = 5):
    """Capture some metrics and save results to the database."""
    # mpstat
    mpstat_host = subprocess.Popen(
        ["just", "mpstat-host", name, str(duration)],
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
    connection = connect_to_db()
    ensure_db(connection, table="mpstat", columns=MPSTAT_COLS)
    ids = parse_mpstat(mpstat_hout, mpstat_gout)
    counters = parse_perf(perf_hout, perf_gout)
    return ids, counters


def parse_mpstat(hout, gout):
    """Parse mpstat output and save to database"""
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


def parse_perf(hout, gout):
    """Parse perf output and return dict of metrics"""
    host_pattern = r"^\s*(\d+)\s+kvm:kvm_exit"
    hmatch = re.search(host_pattern, hout.decode().replace(",", ""), re.MULTILINE)
    if hmatch:
        host_exits = int(hmatch.group(1))
    else:
        print("No match, output: " + hout.decode())
        host_exits = 0
    guest_pattern = pattern = r"^\s*([\d,]+)\s+([\w-]+)"
    matches = re.findall(pattern, gout.decode(), re.MULTILINE)
    metrics = {
        metric.replace("-", "_"): count.replace(",", "") for count, metric in matches
    }
    metrics["vmexits"] = host_exits
    return metrics
