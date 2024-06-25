#!/usr/bin/env python3

from pathlib import Path

SCRIPT_ROOT: Path = Path(__file__).parent.resolve()
PROJECT_ROOT: Path = SCRIPT_ROOT.parent
BUILD_DIR: Path = PROJECT_ROOT / "build"
LINUX_DIR: Path = PROJECT_ROOT / "../linux"
SSH_PORT: int = 2224
DB_PATH = "./bench-result/bench.db"
VM_IP = "172.45.0.2"
VM_REMOTE_IP = "192.168.100.11"
GRAHAM_IP = "192.168.100.20"
