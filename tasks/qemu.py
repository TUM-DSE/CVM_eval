#!/usr/bin/env python3

# Original version:
# https://github.com/Mic92/vmsh/blob/358cd4b6ec7de0dcac05a12e32486ef30658018c/tests/qemu.py

import json
import os
import re
import socket
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from shlex import quote
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterator, List, Text, Optional

from procs import ChildFd, pprint_cmd, run
from config import PROJECT_ROOT


class QmpSession:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.pending_events: Queue[Dict[str, Any]] = Queue()
        self.reader = sock.makefile("r")
        self.writer = sock.makefile("w")
        hello = self._result()
        assert "QMP" in hello, f"Unexpected result: {hello}"
        self.send("qmp_capabilities")

    def _readmsg(self) -> Dict[str, Any]:
        line = self.reader.readline()
        return json.loads(line)

    def _raise_unexpected_msg(self, msg: Dict[str, Any]) -> None:
        m = json.dumps(msg, sort_keys=True, indent=4)
        raise RuntimeError(f"Got unexpected qmp response: {m}")

    def _result(self) -> Dict[str, Any]:
        while True:
            # QMP is in the handshake
            res = self._readmsg()
            if "return" in res or "QMP" in res:
                return res
            elif "event" in res:
                self.pending_events.put(res)
                continue
            else:
                self._raise_unexpected_msg(res)

    def events(self) -> Iterator[Dict[str, Any]]:
        while not self.pending_events.empty():
            yield self.pending_events.get()

        res = self._readmsg()

        if "event" not in res:
            self._raise_unexpected_msg(res)
        yield res

    def send(self, cmd: str, args: Dict[str, str] = {}) -> Dict[str, str]:
        data: Dict[str, Any] = dict(execute=cmd)
        if args != {}:
            data["arguments"] = args

        json.dump(data, self.writer)
        self.writer.write("\n")
        self.writer.flush()
        return self._result()


def is_port_open(ip: str, port: int, wait_response: bool = False) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        if wait_response:
            s.recv(1)
        s.shutdown(2)
        return True
    except Exception:
        return False


@contextmanager
def connect_qmp(path: Path) -> Iterator[QmpSession]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(str(path))

    try:
        yield QmpSession(sock)
    finally:
        sock.close()


def parse_regs(qemu_output: str) -> Dict[str, int]:
    regs = {}
    for match in re.finditer(r"(\S+)\s*=\s*([0-9a-f ]+)", qemu_output):
        name = match.group(1)
        content = match.group(2).replace(" ", "")
        regs[name.lower()] = int(content, 16)
    return regs


def get_ssh_port(session: QmpSession) -> int:
    usernet_info = session.send(
        "human-monitor-command", args={"command-line": "info usernet"}
    )
    ssh_port = None
    for line in usernet_info["return"].splitlines():
        fields = line.split()
        if "TCP[HOST_FORWARD]" in fields and "22" in fields:
            ssh_port = int(line.split()[3])
    assert ssh_port is not None
    return ssh_port


def ssh_cmd(port: int) -> List[str]:
    key_path = PROJECT_ROOT.joinpath("nix", "ssh_key")
    key_path.chmod(0o400)
    return [
        "ssh",
        "-i",
        str(key_path),
        "-p",
        str(port),
        "-oBatchMode=yes",
        "-oStrictHostKeyChecking=no",
        "-oConnectTimeout=5",
        "-oUserKnownHostsFile=/dev/null",
        "root@localhost",
    ]


class QemuVm:
    def __init__(
        self, qmp_session: QmpSession, tmux_session: str, pid: int, config: dict = {}
    ) -> None:
        self.qmp_session = qmp_session
        self.tmux_session = tmux_session
        self.pid = pid
        self.ssh_port = get_ssh_port(qmp_session)
        self.config = config

    def events(self) -> Iterator[Dict[str, Any]]:
        return self.qmp_session.events()

    def wait_for_ssh(self) -> None:
        """
        Block until ssh port is accessible
        """
        print(f"wait for ssh on {self.ssh_port}")
        while True:
            if (
                self.ssh_cmd(
                    ["echo", "ok"],
                    check=False,
                    stderr=subprocess.DEVNULL,
                    verbose=False,
                ).returncode
                == 0
            ):
                break
            time.sleep(0.1)

    def ssh_Popen(
        self,
        stdout: ChildFd = subprocess.PIPE,
        stderr: ChildFd = None,
        stdin: ChildFd = None,
    ) -> subprocess.Popen:
        """
        opens a background process with an interactive ssh session
        """
        cmd = ssh_cmd(self.ssh_port)
        pprint_cmd(cmd)
        return subprocess.Popen(cmd, stdin=stdin, stdout=stdout, stderr=stderr)

    def ssh_cmd(
        self,
        argv: List[str],
        extra_env: Dict[str, str] = {},
        check: bool = True,
        stdin: ChildFd = None,
        stdout: ChildFd = subprocess.PIPE,
        stderr: ChildFd = None,
        verbose: bool = True,
    ) -> "subprocess.CompletedProcess[Text]":
        """
        @return: CompletedProcess.stderr/stdout contains output of `cmd` which
        is run in the vm via ssh.
        """
        env_cmd = []
        if len(extra_env):
            env_cmd.append("env")
            # "-" option makes phoronix-test-suite to complain about mktemp and sh not found
            # TODO: check if this is correct way to handle this
            # env_cmd.append("-")
            for k, v in extra_env.items():
                env_cmd.append(f"{k}={v}")
        cmd = ssh_cmd(self.ssh_port) + ["--"] + env_cmd + [" ".join(map(quote, argv))]
        return run(
            cmd, stdin=stdin, stdout=stdout, stderr=stderr, check=check, verbose=verbose
        )

    def regs(self) -> Dict[str, int]:
        """
        Get cpu register:
        TODO: add support for multiple cpus
        """
        res = self.send(
            "human-monitor-command", args={"command-line": "info registers"}
        )
        return parse_regs(res["return"])

    def dump_physical_memory(self, addr: int, num_bytes: int) -> bytes:
        res = self.send(
            "human-monitor-command",
            args={"command-line": f"xp/{num_bytes}bx 0x{addr:x}"},
        )
        hexval = "".join(
            m.group(1) for m in re.finditer("0x([0-9a-f]{2})", res["return"])
        )
        return bytes.fromhex(hexval)

    def attach(self) -> None:
        """
        Attach to qemu session via tmux. This is useful for debugging
        """
        subprocess.run(["tmux", "-L", self.tmux_session, "attach"])

    def send(self, cmd: str, args: Dict[str, str] = {}) -> Dict[str, str]:
        """
        Send a Qmp command (https://wiki.qemu.org/Documentation/QMP)
        """
        return self.qmp_session.send(cmd, args)

    def pin_vcpu(self, pcpu_base: int = 0) -> None:
        """Pin vCPUs to physical CPUs"""
        cpu_info = self.send("query-cpus-fast")["return"]
        num_cpus = len(cpu_info)
        for cpu in cpu_info:
            tid = cpu["thread-id"]
            cpuidx = cpu["cpu-index"]
            try:
                cmd = ["taskset", "-pc", str(cpuidx + pcpu_base), str(tid)]
                run(cmd)
            except OSError as e:
                print("Failed to pin vCPU{}: {}".format(cpuidx, e))
                return

        iothreads_info = self.send("query-iothreads")["return"]
        num_iothreads = len(iothreads_info)
        if num_iothreads == 0:
            print("No iothreads found")
            return
        print("Pin iothreads")
        for i, cpu in enumerate(iothreads_info):
            tid = cpu["thread-id"]
            try:
                cmd = ["taskset", "-pc", str(pcpu_base + num_cpus + i), str(tid)]
                run(cmd)
            except OSError as e:
                print("Failed to pin vCPU{}: {}".format(cpuidx, e))
                return


@contextmanager
def spawn_qemu(
    qemu_command: List[str],
    extra_args: List[str] = [],
    extra_args_pre: List[str] = [],
    numa_node: Optional[List[int]] = None,
    config: dict = {},
) -> Iterator[QemuVm]:
    with TemporaryDirectory() as tempdir:
        qmp_socket = Path(tempdir).joinpath("qmp.sock")
        cmd = extra_args_pre.copy()

        if numa_node is not None:
            cmd += [
                "numactl",
                f"--cpunodebind={','.join(map(str, numa_node))}",
                f"--membind={','.join(map(str, numa_node))}",
            ]

        qemu_command += [
            "-qmp",
            f"unix:{str(qmp_socket)},server,nowait",
        ]
        cmd += qemu_command
        cmd += extra_args

        print(cmd)

        # run qemu in a tmux session so that we can kill qemu threads easily
        tmux_session = f"pytest-{os.getpid()}"
        tmux = [
            "tmux",
            "-L",
            tmux_session,
            "new-session",
            "-d",
            " ".join(map(quote, cmd)),
        ]
        print("$ " + " ".join(map(quote, tmux)))
        subprocess.run(tmux, check=True)
        try:
            proc = subprocess.run(
                [
                    "tmux",
                    "-L",
                    tmux_session,
                    "list-panes",
                    "-a",
                    "-F",
                    "#{pane_pid}",
                ],
                stdout=subprocess.PIPE,
                check=True,
            )
            qemu_pid = int(proc.stdout)
            print(f"qemu pid: {qemu_pid}")
            while not qmp_socket.exists():
                try:
                    os.kill(qemu_pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    raise Exception("qemu vm was terminated")
            with connect_qmp(qmp_socket) as session:
                yield QemuVm(session, tmux_session, qemu_pid, config)
        finally:
            subprocess.run(["tmux", "-L", tmux_session, "kill-server"])
            while True:
                try:
                    os.kill(qemu_pid, 0)
                except ProcessLookupError:
                    break
                else:
                    print("waiting for qemu to stop")
                    time.sleep(1)
            print("qemu stopped")
