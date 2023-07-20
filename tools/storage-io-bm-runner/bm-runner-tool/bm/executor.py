"""
Excutes `fio` job files
"""
import subprocess


OUTPUT_FLAG = '--output'
OUTPUT_FORMAT_FLAG = '--output-format'
JSON_FORMAT_ARG = 'json'


def run_job(job_file, result_file):
    subprocess.run(['fio', job_file, OUTPUT_FLAG, result_file]) #, OUTPUT_FORMAT_FLAG,
        # JSON_FORMAT_ARG])

