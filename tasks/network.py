import subprocess
from datetime import datetime
from pathlib import Path
from config import PROJECT_ROOT
from tasks.qemu import QemuVm

VM_IP = "172.45.0.2"
NIX_SHELL_PATH = "benchmarks/network/shell.nix"


def run_ping(name: str):
    """Ping the VM.
    The results are saved in ./bench-results/networing/ping/{name}/{date}
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/ping/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    for pkt_size in [64, 128, 256, 512, 1024]:
        cmd = ["nix-shell", f"{NIX_SHELL_PATH}", "--run", f"just run-ping {pkt_size}"]
        output = subprocess.run(cmd, capture_output=True, text=True)
        if output.returncode != 0:
            print(f"Error running ping: {output.stderr}")
            continue
        with open(outputdir_host / f"pkt_size={pkt_size}.log", "w") as f:
            f.write(output.stdout)


def run_iperf(
    name: str,
    vm: QemuVm,
    repeat: int = 1,
):
    """Run the iperf benchmark on the VM.
    The results are saved in ./bench-result/networking/iperf/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/iperf/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    server_cmd = [
        "nix-shell",
        f"/share/{NIX_SHELL_PATH}",
        "--run",
        "just run-iperf-server",
    ]
    vm.ssh_cmd(server_cmd)

    for i in range(repeat):
        print(f"Running iperf {i+1}/{repeat}")
        for pkt_size in [64, 128, 256, 512, 1024]:
            cmd = [
                "nix-shell",
                f"{NIX_SHELL_PATH}",
                "--run",
                f"just run-iperf-client {pkt_size}",
            ]
            output = subprocess.run(cmd, capture_output=True, text=True)
            if output.returncode != 0:
                print(f"Error running ping: {output.stderr}")
                continue
            lines = output.stdout.split("\n")
            with open(outputdir_host / f"{i+1}-{pkt_size}.log", "w") as f:
                f.write("\n".join(lines))
    print(f"Results saved in {outputdir_host}")


def run_memtier(name: str, vm: QemuVm, repeat: int = 1, server: str = "redis"):
    """Run the memtier benchmark on the VM using redis.
    The results are saved in ./bench-result/networking/memtier/redis/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/memtier/redis/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    server_cmd = ["nix-shell", f"/share/{NIX_SHELL_PATH}", "--run", "just run-redis"]
    vm.ssh_cmd(server_cmd)

    for i in range(repeat):
        print(f"Running memtier with {server} {i+1}/{repeat}")
        cmd = ["nix-shell", f"{NIX_SHELL_PATH}", "--run", "just run-memtier-tls"]
        output = subprocess.run(cmd, capture_output=True, text=True)
        if output.returncode != 0:
            print(f"Error running memtier: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{i+1}.log", "w") as f:
            f.write("\n".join(lines))
    print(f"Results saved in {outputdir_host}")


def run_nginx(name: str, vm: QemuVm, repeat: int = 1):
    """Run the nginx on the VM and the wrk benchmark on the host.
    The results are saved in ./bench-result/networking/nginx/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/nginx/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    server_cmd = ["nix-shell", f"/share/{NIX_SHELL_PATH}", "--run", "just run-nginx"]
    vm.ssh_cmd(server_cmd)

    for i in range(repeat):
        print(f"Running wrk {i+1}/{repeat}")
        cmd = ["nix-shell", f"{NIX_SHELL_PATH}", "--run", "just run-wrk"]
        output = subprocess.run(cmd, capture_output=True, text=True)
        if output.returncode != 0:
            print(f"Error running wrk: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{i+1}.log", "w") as f:
            f.write("\n".join(lines))
    print(f"Results saved in {outputdir_host}")
