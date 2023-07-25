from bm import executor
from bm import params
from bm import setup

import io
import logging as log
import random
import string

import click


log.basicConfig(level=log.INFO)


@click.command()
@click.option('--name',
              help='name of the benchmark (else random name selected')
@click.option('--stack',
              required=True,
              type=click.Choice(params.SWStackParam),
              help='P3: sets storage IO stack the benchmark uses')
@click.option('--encryption',
              is_flag=True,
              help='P4: toggles encryption on the selected storage stack')
@click.option('--integrity',
              is_flag=True,
              help='P4.5: toggles integrity protection on the selected storage stack')
@click.option('--storage-level',
              required=True,
              type=click.Choice(params.StorageLevelParam),
              help='P5: sets storage level / granularity')
@click.option('--measurement-type',
              required=True,
              type=click.Choice(params.MeasurementTypeParam),
              help='P6: sets measurement method')
@click.option('--out',
              default='./results.json',
              type=click.File('w'),
              help='result output file')
@click.option('--resource-dir',
              required=True,
              type=click.Path(dir_okay=True, exists=True),
              help='directory to store test resources')

def cli(
        name,
        stack,
        encryption,
        integrity,
        storage_level,
        measurement_type,
        out,
        resource_dir):
    """
    Runs storage IO benchmarks - on a bare-metal host or inside of an optionally
    confidential VM.

    For a description of the benchmark parameters, please refer to
    https://github.com/TUM-DSE/CVM_eval/issues/9.
    """
    rnd_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    if not name:
        name = rnd_id
    else:
        name = f"{name}-{rnd_id}"

    job_file = f'{resource_dir}/fio-job-{name}.ini'
    result_file = f'{resource_dir}/fio-result-{name}.json'

    bm_config = params.BenchmarkConfig(
            stack,
            encryption,
            integrity,
            storage_level,
            measurement_type)
 
    log.info(f"EXECUTING BENCHMARK: <{name}> W/ FOLLOWING PARAMS:")
    log.info(f"P3:      Storage IO Software Stack:  {stack.value}")
    log.info(f"P4:      Encryption:                 {encryption}")
    log.info(f"P4.5:    Integrity:                  {integrity}")
    log.info(f"P5:      Storage Level:              {storage_level}")
    log.info(f"P6:      Measurement Type:           {measurement_type}")
    log.info(f"GENERATED JOB FILE:                  {job_file}")
    log.info(f"GENERATED RESULT FILE:               {result_file}")

    setup.generate_job(bm_config, name, job_file)

    executor.run_job(job_file, result_file)


if __name__ == '__main__':
    cli()
