#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Dict, Iterator, List, Union
import subprocess

import pandas as pd
from lxml import etree
from qemu import QemuVm

# Based on
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
    name: str, identifier: str, benchmark: str, skip_tests: List[str] = []
) -> Command:
    exe = "phoronix-test-suite"
    env = dict(
        TEST_RESULTS_NAME=name,
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
            if identifier == "test":
                continue
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


XML_DIR = Path("/var/lib/phoronix-test-suite/test-results/")


def run_phoronix(
    name: str,
    identifier: str,
    benchmark: str,
    vm: QemuVm,
    skip_tests: List[str] = [],
) -> pd.DataFrame:
    cmd = phoronix_command(name, identifier, benchmark, skip_tests)
    vm.ssh_cmd(cmd.args, extra_env=cmd.env, stdout=None, stdin=yes_please())
    report_path = XML_DIR / f"{name}/composite.xml"
    proc = vm.ssh_cmd(["cat", str(report_path)])
    return parse_xml(proc.stdout)


if __name__ == "__main__":
    import sys

    if len(sys.argv) <= 1:
        print("Usage: python phoronix.py <xml file>")
        sys.exit(1)
    xml_file = Path(sys.argv[1])
    df = parse_xml(xml_file)
    print(df.to_string())
