#!/usr/bin/env python3

from pathlib import Path

SCRIPT_ROOT: Path = Path(__file__).parent.resolve()
PROJECT_ROOT: Path = SCRIPT_ROOT.parent
BUILD_DIR: Path = PROJECT_ROOT / "build"
LINUX_DIR: Path = PROJECT_ROOT / "../linux"
SSH_PORT: int = 2224
VM_IP = "172.45.0.2"
