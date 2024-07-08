from datetime import datetime
from typing import Any, Optional, List
from pathlib import Path
import os
import re
import subprocess
import time

from config import PROJECT_ROOT
from qemu import spawn_qemu, QemuVm


def boot_test(qemu_cmd: List[str], pin: bool, outfile=None, **kargs: Any) -> None:
    """Start a VM and wait for the VM to boot and then terminate the VM."""
    resource = kargs["config"]["resource"]
    vmconfig = kargs["config"]["vmconfig"]
    pin_base: int = kargs["config"].get("pin_base", resource.pin_base)
    trace: bool = kargs["config"].get("boot_trace", True)

    if trace:
        trace_script = f"{PROJECT_ROOT}/benchmarks/boottime/boot_time_eval.bt"
        code = []
        qemu_path = Path(vmconfig.qemu)
        # QEMU built with nix is wrapped. Get the actual binary path to trace
        if os.listdir(qemu_path.parent).count(".qemu-system-x86_64-wrapped") > 0:
            qemu_path = qemu_path.parent / ".qemu-system-x86_64-wrapped"
        # replace the qemu path in the bpftrace script
        pat = re.compile(r"(ur?):.*qemu-system-x86_64.*:(.*)")
        with open(trace_script) as f:
            for line in f.readlines():
                m = pat.match(line)
                if m:
                    new_path = f"{m.group(1)}:{qemu_path}:{m.group(2)}"
                    line = line.replace(m.group(0), new_path)
                code.append(line.encode())

        cmd = ["bpftrace", "-"]  # read program code from stdin
        bpftrace = subprocess.Popen(
            cmd,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        bpftrace.stdin.writelines(code)
        bpftrace.stdin.close()  # send EOF
        time.sleep(3)  # ensure loading of BPF program

    vm: QemuVM
    with spawn_qemu(
        qemu_cmd, numa_node=resource.numa_node, config=kargs["config"]
    ) as vm:
        if pin:
            vm.pin_vcpu(pin_base)
        time.sleep(10)
        vm.wait_for_ssh()
        vm.shutdown()

    # get output from bpftrace process
    if trace:
        bpftrace.terminate()
        bpftrace.wait()
        if bpftrace.returncode != 0:
            err = bpftrace.stderr.read().decode()
            print(f"bpftrace failed with return code {bpftrace.returncode}")
            print(err)
        if outfile:
            with open(outfile, "w") as f:
                f.write(bpftrace.stdout.read().decode())


def run_boot_test(
    name: str, qemu_cmd: List[str], pin: bool, outfile=None, **kargs: Any
) -> None:
    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    repeat: int = kargs["config"].get("repeat", 1)
    trace: bool = kargs["config"].get("boot_trace", True)

    outputdir = Path(f"{PROJECT_ROOT}/bench-result/boottime/{name}/{date}")
    if trace:
        outputdir.mkdir(parents=True, exist_ok=True)

    for i in range(repeat):
        outfile = outputdir / f"{i+1}.txt"
        boot_test(qemu_cmd, pin, outfile, **kargs)
        time.sleep(1)

    if trace:
        print(f"Output written to {outputdir}")
