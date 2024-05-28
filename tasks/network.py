import subprocess
from datetime import datetime
from pathlib import Path
import subprocess
import time

from config import PROJECT_ROOT, VM_IP
from qemu import QemuVm


def run_ping(name: str, vm: QemuVm):
    """Ping the VM.
    The results are saved in ./bench-results/networing/ping/{name}/{date}
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/ping/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    for pkt_size in [64, 128, 256, 512, 1024]:
        process = subprocess.Popen(
            f"ping -c 30 -i0.1 -s {pkt_size} {VM_IP}".split(" "),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        stdout, stderr = process.communicate()
        exit_code = process.wait()

        if exit_code != 0:
            print(f"Error running ping: {stderr}")
            continue

        with open(outputdir_host / f"{pkt_size}.log", "wb") as f:
            f.write(stdout)

    print(f"Results saved in {outputdir_host}")


def run_iperf(
    name: str,
    vm: QemuVm,
    udp: bool = False,
    port: int = 7175,
    parallel: int = 8,  # number of parallel streams
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
        output = subprocess.check_output(cmd).decode()
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
    tls: bool = False,
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
        "--repair",
        "--run",
        f"just STANDARD_MEMTIER_PORT={port} TLS_MEMTIER_PORT={tls_port} THREADS={server_threads} run-{server}{tls_}",
    ]
    vm.ssh_cmd(server_cmd)
    print("Server started")
    time.sleep(1)

    if tls:
        cmd = [
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


def run_nginx(name: str, vm: QemuVm):
    """Run the nginx on the VM and the wrk benchmark on the host.
    The results are saved in ./bench-result/networking/nginx/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/nginx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    nix_shell_path = "benchmarks/network/shell.nix"

    server_cmd = ["nix-shell", f"/share/{nix_shell_path}", "--run", "just run-nginx"]
    vm.ssh_cmd(server_cmd)
    time.sleep(1)

    # HTTP
    cmd = ["wrk", f"http://{VM_IP}"]
    print(cmd)
    output = subprocess.run(cmd, capture_output=True, text=True)
    if output.returncode != 0:
        print(f"Error running wrk: {output.stderr}")
    lines = output.stdout.split("\n")
    with open(outputdir_host / f"http.log", "w") as f:
        f.write("\n".join(lines))

    # HTTPS
    cmd = ["wrk", f"https://{VM_IP}"]
    print(cmd)
    output = subprocess.run(cmd, capture_output=True, text=True)
    if output.returncode != 0:
        print(f"Error running wrk: {output.stderr}")
    lines = output.stdout.split("\n")
    with open(outputdir_host / f"https.log", "w") as f:
        f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")
