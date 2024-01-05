#!/usr/bin/env python3
import os
from typing import Any

from invoke import task

# constants
DEFAULT_NATIVE_SSH_FORWARD_PORT = 2222
DEFAULT_SEV_SSH_FORWARD_PORT = 2223

REPO_DIR = os.path.dirname(os.path.realpath(__file__))
SSH_KEY = os.path.join(REPO_DIR, "nix", "ssh_key")


# helpers
def ssh_vm(c: Any, ssh_port: int) -> None:
    c.run(f"ssh -i {SSH_KEY} -o 'StrictHostKeyChecking no' -p {ssh_port} root@localhost", pty=True)

# tasks
@task(help={"ssh_port": "port to connect ssh to"})
def ssh_native_vm(c: Any, ssh_port: int = DEFAULT_NATIVE_SSH_FORWARD_PORT) -> None:
    """
    SSH into the native VM.
    """
    ssh_vm(c, ssh_port)

