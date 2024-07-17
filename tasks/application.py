#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
from typing import Optional
from subprocess import CalledProcessError

from config import PROJECT_ROOT
from qemu import QemuVm
from storage import mount_disk


def setup_disk(vm: QemuVm) -> bool:
    """Check if virtio-blk (/dev/vdb) is available. If so, prepare the disk for the evaluation"""
    if vm.config["virtio_blk"] is None:
        return False

    r = mount_disk(vm, "/dev/vdb", "/mnt", format="auto")
    if not r:
        return False
    output = vm.ssh_cmd(["rsync", "-a", "/share/benchmarks/application", "/mnt/"])
    if output.returncode != 0:
        print("rsync error")
        return False

    return True


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

    disk = setup_disk(vm)
    if disk:
        rootdir = "/mnt/application"
    else:
        rootdir = "/share/benchmarks/application"

    cmd = [
        "just",
        "-f",
        f"{rootdir}/blender/justfile",
        "run",
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

    disk = setup_disk(vm)
    if disk:
        rootdir = "/mnt/application"
    else:
        rootdir = "/share/benchmarks/application"

    cmd = [
        "just",
        "-f",
        f"{rootdir}/tensorflow/justfile",
        "run",
        f"{thread_cnt}",
    ]

    for i in range(repeat):
        print(f"Running tensorflow {i+1}/{repeat}")
        try:
            output = vm.ssh_cmd(cmd)
        except CalledProcessError as e:
            # Tensorflow may fail due to OOM, ignore that case
            print(f"Error running tensorflow: {e}")
            continue
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

    disk = setup_disk(vm)
    if disk:
        rootdir = "/mnt/application"
    else:
        rootdir = "/share/benchmarks/application"

    cmd = [
        "just",
        "-f",
        f"{rootdir}/pytorch/justfile",
        "run",
        f"{thread_cnt}",
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

    disk = setup_disk(vm)
    if disk:
        rootdir = "/mnt/application"
    else:
        rootdir = "/share/benchmarks/application"

    def init():
        cmd = [
            "just",
            "-f",
            f"{rootdir}/sqlite/justfile",
            f"DBPATH={dbpath}",
            "init",
        ]
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error running sqlite: {output.stderr}")
            return

    def run(test: str):
        cmd = [
            "just",
            "-f",
            f"{rootdir}/sqlite/justfile",
            f"DBPATH={dbpath}",
            f"run_{test}",
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


def prepare(vm: QemuVm):
    for app in ["pytorch", "tensorflow"]:
        cmd = [
            "just",
            "-f",
            f"/share/benchmarks/application/{app}/justfile",
            "prepare",
        ]
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error preparing {app}: {output.stderr}")
