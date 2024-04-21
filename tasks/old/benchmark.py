# run bare metal benchmarks
import os
import time
from typing import Any

from invoke import task

from common import EVAL_NVME_PATH, FIO_HOST_VM_OUTPUT_DIR, FIO_POSSIBLE_BENCHMARKS, REPO_DIR, build_fio_cmd, print_and_sudo, warn_nvm_use
from tasks.utils import CRYPTSETUP_TARGET_NAME, CRYPTSETUP_TARGET_PATH, cryptsetup_open

DEFAULT_FIO_JOB_FILE = os.path.join(REPO_DIR, "bm", "blk-bm.fio")


@task(help={
    "path_to_ssd": "path to the ssd to benchmark",
    "dm_benchmark": f"whether to benchmark the device mapper (opens cryptsetup on the ssd if not available at {CRYPTSETUP_TARGET_PATH})",
    "fio_benchmark": f"which fio benchmark to run (default: all) (macros: {', '.join(FIO_POSSIBLE_BENCHMARKS)})",
    "fio_job_path": f"path to fio job file (default: {DEFAULT_FIO_JOB_FILE})"
    })
def exec_fio_bare_metal(
        c: Any,
        path_to_ssd: str = EVAL_NVME_PATH,
        dm_benchmark: bool = False,
        fio_benchmark: str = "all",
        fio_job_path: str = DEFAULT_FIO_JOB_FILE,
        ) -> None:
    """
    Run fio on the bare metal machine nvme ssd.
    """

    fio_output_path: str = FIO_HOST_VM_OUTPUT_DIR


    if dm_benchmark:
        if not os.path.exists(CRYPTSETUP_TARGET_PATH):
            cryptsetup_open(c, path_to_ssd, CRYPTSETUP_TARGET_NAME)
        fio_filename = CRYPTSETUP_TARGET_PATH
        cmd_log_name = "bm-crypt"
    else:
        fio_filename = path_to_ssd
        cmd_log_name = "bm"


    warn_nvm_use(nvme_id=path_to_ssd)

    cmd_log_name += f"-{time.strftime('%Y-%m-%d-%H-%M')}.json"
    fio_output_path = os.path.join(fio_output_path, cmd_log_name)

    fio_cmd: str = build_fio_cmd(
        fio_benchmark=fio_benchmark,
        fio_filename=fio_filename,
        fio_job_path=fio_job_path,
        fio_output_path=fio_output_path)

    print_and_sudo(c, fio_cmd, pty=True)
