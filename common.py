#!/usr/bin/env python3
import os

REPO_DIR = os.path.dirname(os.path.realpath(__file__))

def print_and_run(c, cmd):
    print(cmd)
    c.run(cmd)


# private
def _get_nix_rev():
    return os.popen("nix eval --raw .#lib.nixpkgsRev 2>/dev/null").read().strip()

# private func dependent constants
NIX_RESULTS_DIR = os.path.join(REPO_DIR, ".git", "nix-results", f"{_get_nix_rev()}")
