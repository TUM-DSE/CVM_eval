#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from typing import Optional

from config import PROJECT_ROOT
from qemu import QemuVm


def run_blender(
    name: str,
    vm: QemuVm,
    repeat: int = 1,
):
    """Run the blender benchmark on the VM.
    The results are saved in ./bench-result/application/blender/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/application/blender/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    cmd = [
        "nix-shell",
        "/share/benchmarks/application/blender/shell.nix",
        "--repair",
        "--run",
        "just run",
    ]

    for i in range(repeat):
        print(f"Running blender {i+1}/{repeat}")
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running blender: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{i+1}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_tensorflow(
    name: str,
    vm: QemuVm,
    repeat: int = 1,
    thread_cnt: Optional[int] = None,
):
    """Run the tensorflow benchmark on the VM.
    The results are saved in ./bench-result/application/tensorflow/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/application/tensorflow/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    if thread_cnt is None:
        if "resource" in vm.config:
            # use the number of CPUs as the default thread count
            thread_cnt = vm.config["resource"].cpu
        else:
            thread_cnt = 1

    cmd = [
        "nix-shell",
        "/share/benchmarks/application/tensorflow/shell.nix",
        "--repair",
        "--run",
        f"just run {thread_cnt}",
    ]

    for i in range(repeat):
        print(f"Running tensorflow {i+1}/{repeat}")
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running tensorflow: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"thread_{thread_cnt}-{i+1}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_pytorch(
    name: str,
    vm: QemuVm,
    repeat: int = 1,
    thread_cnt: Optional[int] = None,
):
    """Run the pytorch benchmark on the VM.
    The results are saved in ./bench-result/application/pytorch/{name}/{date}/
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/application/pytorch/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    if thread_cnt is None:
        if "resource" in vm.config:
            # use the number of CPUs as the default thread count
            thread_cnt = vm.config["resource"].cpu
        else:
            thread_cnt = 1

    cmd = [
        "nix-shell",
        "/share/benchmarks/application/pytorch/shell.nix",
        "--repair",
        "--run",
        f"just run {thread_cnt}",
    ]

    for i in range(repeat):
        print(f"Running pytorch {i+1}/{repeat}")
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running pytorch: {output.stderr}")
            continue
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"thread_{thread_cnt}-{i+1}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host}")


def run_sqlite(
    name: str,
    vm: QemuVm,
    dbpath: str = "/tmp/test.db",
):
    """Run the SQLite's kvtest
    The results are saved in ./bench-result/application/sqlite/{name}/{date}/[seq,rand,update_seq,update_rand].log
    """
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputdir = Path(f"./bench-result/application/sqlite/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    def init():
        cmd = [
            "nix-shell",
            "/share/benchmarks/application/sqlite/shell.nix",
            "--repair",
            "--run",
            f"just DBPATH={dbpath} init",
        ]
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running sqlite: {output.stderr}")
            return

    def run(test: str):
        cmd = [
            "nix-shell",
            "/share/benchmarks/application/sqlite/shell.nix",
            "--repair",
            "--run",
            f"just DBPATH={dbpath} run_{test}",
        ]
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running sqlite: {output.stderr}")
            return output.stdout

        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{test}.log", "w") as f:
            f.write("\n".join(lines))

    init()
    run("seq")
    run("rand")
    run("update")
    run("update_rand")

    print(f"Results saved in {outputdir_host}")
