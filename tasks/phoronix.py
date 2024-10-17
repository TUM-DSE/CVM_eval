#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import IO, Dict, Iterator, List, Union
import subprocess

import pandas as pd
from lxml import etree

from config import PROJECT_ROOT
from qemu import QemuVm

# Based on
# (c) 2021-2022 Jörg Thalheim
# https://github.com/Mic92/vmsh/blob/358cd4b6ec7de0dcac05a12e32486ef30658018c/tests/measure_phoronix.py


@dataclass
class Command:
    args: List[str]
    env: Dict[str, str]

    @property
    def env_vars(self) -> List[str]:
        env_vars = []
        for k, v in self.env.items():
            env_vars.append(f"{k}={v}")
        return env_vars


def phoronix_command(
    result_dir_name: str, identifier: str, benchmark: str, skip_tests: List[str] = []
) -> Command:
    exe = "phoronix-test-suite"
    env = dict(
        TEST_RESULTS_NAME=result_dir_name,
        TEST_RESULTS_IDENTIFIER=identifier,
        TEST_RESULTS_DESCRIPTION="",
        # no auto-updates
        http_proxy="127.0.1.2:28201",
    )
    env["SKIP_TESTS"] = ",".join(skip_tests)

    return Command([str(exe), "batch-run", benchmark], env)


def yes_please() -> IO[bytes]:
    yes_please = subprocess.Popen(["yes"], stdout=subprocess.PIPE)
    assert yes_please.stdout is not None
    return yes_please.stdout


def parse_xml(path: Union[str, Path]) -> pd.DataFrame:
    """Parse the Phoronix XML file (or str) and return a DataFrame with the results."""
    if isinstance(path, Path):
        tree = etree.parse(str(path))
    else:
        tree = etree.fromstring(path)
    results = defaultdict(list)
    for result in tree.xpath("./Result"):
        for entry in result.xpath("./Data/Entry"):
            value = entry.xpath("./Value")[0].text
            if value == None:
                # the value can be None if the test failed to run
                printf(f"XXX: value of {entry} is None! check the xml file")
                continue
            identifier = entry.xpath("./Identifier")[0].text
            results["identifier"].append(entry.xpath("./Identifier")[0].text)
            results["value"].append(float(entry.xpath("./Value")[0].text))
            results["raw_string"].append(entry.xpath("./RawString")[0].text)
            json = entry.xpath("./JSON")
            if len(json) == 0:
                results["json"].append("")
            else:
                results["json"].append(json[0].text)

            title = result.xpath("./Title")[0].text
            scale = result.xpath("./Scale")[0].text
            description = result.xpath("./Description")[0].text

            results["title"].append(title)
            results["app_version"].append(result.xpath("./AppVersion")[0].text)
            results["description"].append(description)
            results["scale"].append(scale)

            results["proportion"].append(result.xpath("./Proportion")[0].text)
            results["benchmark_id"].append("%s: %s [%s]" % (title, description, scale))

    return pd.DataFrame(results)


# test results path when running phoronix as root
XML_DIR = Path("/var/lib/phoronix-test-suite/test-results/")


def install_bench(bench_name: str, vm: QemuVm):
    """Install the benchmark suite on the VM"""
    # vm.ssh_cmd(["phoronix-test-suite", "install", bench_name], stdin=yes_please())
    # XXX: for some reason, mpif90 is missing even though mpi is already installed. why?
    vm.ssh_cmd(
        [
            "nix-shell",
            "-p",
            "mpi",
            "--run",
            f"phoronix-test-suite install {bench_name}",
        ],
        stdin=yes_please(),
    )


def run_phoronix(
    name: str,  # vm name, e.g., snp-direct-medium
    bench_name: str,  # name for the result directory
    pts_name: str,  # bench mark suite name e.g., "pts/memory"
    vm: QemuVm,
    skip_tests: List[str] = [],
):
    """Run phoronix-test-suite (pts) on the VM

    # How to run pts without prompts
    By default, pts shows several prompts for the configuration.
    We can suppress prompts using "batch-run". In this case, we need to
    properly write configuration in the /etc/phoronix-test-suite.xml (when
    running pts as root) (or configure the file with "batch-setup" command).

    {PROJECT_ROOT}/config/phoronix/phoronix-test-suite.xml contains the
    configuration (especially see <BATCH_MODE> section). The file is copied to
    the VM file system when building the guest image.

    With batch-mode, pts uses the following environment variables
    - TEST_RESULTS_NAME
    - TEST_RESULTS_IDENTIFIER

    # Benchmark results
    (when running as root), pts saves results in
    /var/lib/phoronix-test-suite/test-results/{TEST_RESULTS_NAME}/composite.xml
    In the composite.xml, the results are saved with TEST_RESULTS_IDENTIFIER.
    If you run the same benchmark with the same TEST_RESULTS_NAME but with
    different TEST_RESULTS_IDENTIFIER, pts automatically merges the results
    and save them in the same composite.xml.

    # Saving results
    One usual way to save results would be using the same TEST_RESULTS_NAME but with
    different TEST_RESULTS_IDENTIFIER (e.g., "vm", "snp", ...).
    This script, instead, saves results using the benchmark running time
    as a TEST_RESULTS_NAME, i.e., it saves results to ./test-results/{date}/composite.xml
    Then copy the result to {PROJECT_ROOT}/bench-result/phoronix/{name}/{bench_name}/{date}.xml
    Reason
    - it makes it easier to manage benchmark results per VM configuration
    - we can save multiple run results for the same benchmark
    """

    date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    result_dir_name = f"{date}"
    identifier = f"{name}"  # use the vm name as the identifier

    cmd = phoronix_command(result_dir_name, identifier, pts_name, skip_tests)
    vm.ssh_cmd(cmd.args, extra_env=cmd.env, stdout=None, stdin=yes_please())

    report_path = XML_DIR / f"{result_dir_name}/composite.xml"
    outputdir = Path(f"./bench-result/phoronix/{name}/{bench_name}/")
    outputdir_host = PROJECT_ROOT / outputdir
    outputdir_host.mkdir(parents=True, exist_ok=True)
    out_path = Path("/share") / outputdir / f"{date}.xml"

    # copy the result to the host
    vm.ssh_cmd(["cp", str(report_path), str(out_path)])


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 1:
        print("Usage: python phoronix.py <xml file>")
        sys.exit(1)
    xml_file = Path(sys.argv[1])
    df = parse_xml(xml_file)
    print(df.to_string())
