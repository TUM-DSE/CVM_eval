#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
import multiprocessing
import time
from typing import Optional

from config import PROJECT_ROOT, DATE_FORMAT
from qemu import QemuVm
from storage import mount_disk
from utils import (
    NPB_COLS,
    capture_metrics,
    ensure_db,
    insert_into_db,
    connect_to_db,
    TENSORFLOW_COLS,
)


def setup_disk(vm: QemuVm, fail_stop=True) -> bool:
    """Check if virtio-blk (/dev/vdb) is available. If so, prepare the disk for the evaluation"""
    if vm.config["virtio_blk"] is None:
        return False

    r = mount_disk(vm, "/dev/vdb", "/mnt", format="auto")
    if not r:
        if fail_stop:
            raise Exception("Failed to mount virtio-blk")
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
    metrics: bool = False,
):
    """Run the tensorflow benchmark on the VM.
    The results are saved in ./bench-result/application/tensorflow/{name}/{date}/
    """
    date = datetime.now().strftime(DATE_FORMAT)
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
        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(
            target=run_benchmark, args=(child_conn, vm, cmd)
        )
        process.start()
        time.sleep(3)
        # Scan the logfile for start of the benchmark
        if scan_file_for_sequence(f"{PROJECT_ROOT}/tensorflow.log", "Start iteration"):
            print("Benchmark started")
        else:
            print("Timeout: Benchmark not started")
            return
        time.sleep(15)
        mpstat_ids, perf_ids, bpf_id = (
            capture_metrics(name, 5) if metrics else ((None, None), (None, None))
        )
        process.join()
        output = parent_conn.recv()
        # parse output and save to db
        pattern = r"Total throughput \(examples/sec\): (\d+\.\d+)"
        match = re.search(pattern, output.stdout)
        if match:
            examples = match.group(1)
            print(f"Total throughput (examples/sec): {examples}")
            connection = connect_to_db()
            ensure_db(connection, table="tensorflow", columns=TENSORFLOW_COLS)
            insert_into_db(
                connection,
                "tensorflow",
                {
                    "date": date,
                    "name": name,
                    "examples_per_sec": examples,
                    "thread_cnt": thread_cnt,
                    "mpstat_host": mpstat_ids[0],
                    "mpstat_guest": mpstat_ids[1],
                    "perf_host": perf_ids[0],
                    "perf_guest": perf_ids[1],
                    "bpf": bpf_id,
                },
            )
        else:
            print(f"No Match in output: {output.stdout}")
            continue
        if output.returncode != 0:
            print(f"Error running tensorflow: {output.stderr}")
            continue
        with open(outputdir_host / f"thread_{thread_cnt}-{i+1}.log", "w") as f:
            f.write(output.stdout)
    print(f"Results saved in {outputdir_host} and database")


def run_npb(
    name: str, vm: QemuVm, prog: str = "ua", size: str = "C", metrics: bool = False
):
    """Run the NPB benchmark on the VM.
    The results are saved in ./bench-result/application/npb/{name}/{date}/ and the database
    """
    date = datetime.now().strftime(DATE_FORMAT)
    outputdir = Path(f"./bench-result/application/npb/{name}/{date}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)

    root_dir = "/share/benchmarks/application"

    connection = connect_to_db()
    ensure_db(connection, table="npb", columns=NPB_COLS)
    for policy in ["ACTIVE", "PASSIVE"]:
        cmd = [
            "just",
            "-f",
            f"{root_dir}/npb/justfile",
            "run",
            f"{prog}",
            f"{policy}",
        ]
        print(f"Running NPB {prog} {size}, policy: {policy}")
        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(
            target=run_benchmark, args=(child_conn, vm, cmd)
        )
        process.start()
        mpstat_ids, perf_ids, bpf_id = (
            capture_metrics(name, 1) if metrics else ((None, None), (None, None))
        )
        process.join()
        output = parent_conn.recv()
        pattern = r"Time in seconds\s*=\s*([\d.]+).*?Mop/s total\s*=\s*([\d.]+)"
        match = re.search(pattern, output.stdout, re.DOTALL)
        if match:
            time, mops = match.groups()
            print(f"Time in seconds: {time}, Mop/s total: {mops}")
            insert_into_db(
                connection,
                "npb",
                {
                    "date": date,
                    "name": name,
                    "prog": prog,
                    "size": size,
                    "policy": policy,
                    "threads": vm.config["resource"].cpu,
                    "time": time,
                    "mops": mops,
                    "mpstat_host": mpstat_ids[0],
                    "mpstat_guest": mpstat_ids[1],
                    "perf_host": perf_ids[0],
                    "perf_guest": perf_ids[1],
                    "bpf": bpf_id,
                },
            )

        else:
            print(f"No Match in output: {output.stdout}")
            return
        if output.returncode != 0:
            print(f"Error running NPB: {output.stderr}")
            return
        lines = output.stdout.split("\n")
        with open(outputdir_host / f"{prog}_{size}_{policy}.log", "w") as f:
            f.write("\n".join(lines))

    print(f"Results saved in {outputdir_host} and database")


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
    for app in ["pytorch", "tensorflow", "npb"]:
        cmd = [
            "just",
            "-f",
            f"/share/benchmarks/application/{app}/justfile",
            "prepare",
        ]
        output = vm.ssh_cmd(cmd)
        if output.returncode != 0:
            print(f"Error preparing {app}: {output.stderr}")


# Scan file for 120 seconds
def scan_file_for_sequence(file_path, sequence):
    start_time = time.time()
    while time.time() - start_time < 5 * 60:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                for line in file.readlines():
                    if sequence in line:
                        return True
    return False


def run_benchmark(pipe, vm, cmd):
    output = vm.ssh_cmd(cmd)
    pipe.send(output)
