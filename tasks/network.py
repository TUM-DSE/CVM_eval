import subprocess
from datetime import datetime
from pathlib import Path
import subprocess
import time

from config import PROJECT_ROOT, VM_IP, VM_REMOTE_IP
from qemu import QemuVm


def run_ping(name: str, vm: QemuVm, remote: bool = False):
    """Ping the VM.
    The results are saved in ./bench-results/networing/ping/{name}/{date}
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/ping/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    host_ip = VM_REMOTE_IP if remote else VM_IP
    for pkt_size in [64, 128, 256, 512, 1024]:
        cmd = ["ping", "-c", "30", "-i0.1", "-s", f"{pkt_size}", host_ip]
        output = (
            remote_ssh_cmd(cmd) if remote else subprocess.check_output(cmd).decode()
        )
        lines = output.split("\n")
        with open(outputdir_host / f"{pkt_size}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


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
