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
        for pkt_size in [64, 128, 256, 512, 1024]:
            print(f"Running iperf {i+1}/{repeat}")
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
            print(cmd)
            if udp:
                cmd.append("-u")
            output = subprocess.check_output(cmd)
            if output.returncode != 0:
                print(f"Error running iperf: {output.stderr}")
                continue
            lines = output.stdout.split("\n")
            with open(outputdir_host / f"{i+1}.log", "w") as f:
                f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")
    vm.ssh_cmd("poweroff")


def run_memtier(name: str, vm: QemuVm, repeat: int = 1, server: str = "redis"):
    """Run the memtier benchmark on the VM using redis.
    The results are saved in ./bench-result/networking/memtier/redis/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/networking/memtier/redis/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    server_cmd = [
        "nix-shell",
        "/share/benchmarks/network/memtier/shell.nix",
        "--run",
        f"just run-{server}",
    ]
    vm.ssh_cmd(server_cmd)

    port = 6379
    threads = 4

    for i in range(repeat):
        print(f"Running memtier redis {i+1}/{repeat}")
        cmd = [
            "memtier_benchmark",
            f"--host={VM_IP}",
            "-p",
            f"{port}",
            "-t",
            f"{threads}",
        ]
        output = subprocess.check_output(cmd)
        if output.returncode != 0:
            print(f"Error running memtier: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{i+1}.log", "w") as f:
            f.write("\n".join(lines))
        vm.ssh_cmd("poweroff")


# def run_memtier_memcached(name: str, vm: QemuVm, repeat: int = 1, mode: str = "binary"):
#     """Run the memtier benchmark on the VM using memcached.
#     The results are saved in ./bench-result/networking/memtier/memcached/{mode}/{name}/{date}/
#     """
#     date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
#     outputdir = Path(
#         f"./bench-result/networking/memtier/memcached/{mode}/{name}/{date}/")
#     outputdir_host = PROJECT_ROOT / outputdir
#     outputdir_host.mkdir(parents=True, exist_ok=True)
