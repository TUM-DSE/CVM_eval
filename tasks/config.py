#!/usr/bin/env python3

from pathlib import Path

SCRIPT_ROOT: Path = Path(__file__).parent.resolve()
PROJECT_ROOT: Path = SCRIPT_ROOT.parent

BUILD_DIR: Path = PROJECT_ROOT / "build"
