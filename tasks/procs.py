#!/usr/bin/env python3

# Based on
# https://github.com/Mic92/vmsh/blob/358cd4b6ec7de0dcac05a12e32486ef30658018c/tests/procs.py

import os
import subprocess
from pathlib import Path
from typing import IO, Dict, List, Optional, Text, Union

ChildFd = Union[None, int, IO]


def pprint_cmd(cmd: List[str], extra_env: Dict[str, str] = {}) -> None:
    env_string = []
    for k, v in extra_env.items():
        env_string.append(f"{k}={v}")
    print(f"$ {' '.join(env_string + cmd)}", flush=True)


def run(
    cmd: List[str],
    extra_env: Dict[str, str] = {},
    stdout: ChildFd = subprocess.PIPE,
    stderr: ChildFd = None,
    input: Optional[str] = None,
    stdin: ChildFd = None,
    check: bool = True,
    verbose: bool = True,
    cwd: Optional[Path] = None,
) -> "subprocess.CompletedProcess[Text]":
    env = os.environ.copy()
    env.update(extra_env)
    if verbose:
        pprint_cmd(cmd, extra_env)
    return subprocess.run(
        cmd,
        stdout=stdout,
        stderr=stderr,
        check=check,
        env=env,
        text=True,
        input=input,
        stdin=stdin,
        cwd=cwd,
    )
