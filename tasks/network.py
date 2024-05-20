import subprocess
from datetime import datetime
from pathlib import Path
from config import PROJECT_ROOT
from tasks.qemu import QemuVm

VM_IP = "172.45.0.2"


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
            f"ping -c 20 -s {pkt_size} {VM_IP}".split(" "),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        exit_code = process.wait()

        if exit_code != 0:
            print(f"Error running ping: {stderr}")
            continue

        with open(outputdir_host / f"pkg_size={pkt_size}.log", "wb") as f:
            f.write(stdout)


def run_iperf(
    name: str,
    vm: QemuVm,
    repeat: int = 1,
    udp: bool = False,
):
    """Run the iperf benchmark on the VM.
    The results are saved in ./bench-result/networking/iperf/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/iperf/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    port = 7175

    server_cmd = ["iperf", "-s", "-p", f"{port}", "-D"]
    vm.ssh_cmd(server_cmd)
    streams = 1

    for i in range(repeat):
        print(f"Running iperf {i+1}/{repeat}")
        for pkt_size in [64, 128, 256, 512, 1024]:
            cmd = [
                "iperf",
                "-c",
                f"{VM_IP}",
                "-p",
                f"{port}",
                "-l",
                f"{pkt_size}",
                "-P",
                f"{streams}",
            ]
            if udp:
                cmd.append("-u")
            output = subprocess.run(cmd, capture_output=True, text=True)
            if output.returncode != 0:
                print(f"Error running ping: {output.stderr}")
                continue
            lines = output.stdout.split("\n")
            with open(outputdir_host / f"{i+1}-{pkt_size}.log", "w") as f:
                f.write("\n".join(lines))
    print(f"Results saved in {outputdir_host}")


def run_memtier(
    name: str, vm: QemuVm, repeat: int = 1, server: str = "redis", tls: bool = False
):
    """Run the memtier benchmark on the VM using redis.
    The results are saved in ./bench-result/networking/memtier/redis/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/memtier/redis/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    nix_shell_path = "benchmarks/network/memtier/shell.nix"

    server_cmd = ["nix-shell", f"/share/{nix_shell_path}", "--run", "just run-redis"]
    vm.ssh_cmd(server_cmd)

    standard_port = 6379
    tls_port = 6380
    port = tls_port if tls else standard_port
    threads = 4

    for i in range(repeat):
        print(f"Running memtier with redis {i+1}/{repeat}")
        cmd = ["nix-shell", f"{nix_shell_path}", "--run", "just run-memtier-tls"]
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

    nix_shell_path = "benchmarks/network/nginx/shell.nix"

    server_cmd = ["nix-shell", f"/share/{nix_shell_path}", "--run", "just run-nginx"]
    vm.ssh_cmd(server_cmd)

    for i in range(repeat):
        print(f"Running wrk {i+1}/{repeat}")
        cmd = ["nix-shell", f"{nix_shell_path}", "--run", "just run-wrk"]
        output = subprocess.run(cmd, capture_output=True, text=True)
        if output.returncode != 0:
            print(f"Error running wrk: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{i+1}.log", "w") as f:
            f.write("\n".join(lines))
    print(f"Results saved in {outputdir_host}")
