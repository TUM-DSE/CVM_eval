"""
Excutes `fio` job files
"""
import subprocess


OUTPUT_FLAG = '--output'
OUTPUT_FORMAT_FLAG = '--output-format'
JSON_FORMAT_ARG = 'json'
NORMAL_FORMAT_ARG = 'normal'
CS_FORMAT_LIST_ARG = f"{JSON_FORMAT_ARG},{NORMAL_FORMAT_ARG}"


def run_job(job_file, result_file):
    sp = subprocess.run(['fio', job_file, OUTPUT_FLAG, result_file,
         OUTPUT_FORMAT_FLAG, f"{CS_FORMAT_LIST_ARG}"])
    sp.check_returncode()

