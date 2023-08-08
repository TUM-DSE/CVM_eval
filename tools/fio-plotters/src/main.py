import os
from pathlib import Path

from plot import json_parser, plotter

import click


GLOB_PATTERN_POSTFIX = '*fio*.json'

@click.command()
@click.option('--fio-input-dirs',
              required=True,
              type=click.Path(dir_okay=True, exists=True),
              multiple=True,
              help='input benchmark fio json file dirs; searches recursively for pattern `*fio*.json`')
@click.option('--output-dir',
              type=click.Path(dir_okay=True, exists=True),
              help='dir to which to output plots')
def cli(
        fio_input_dirs,
        output_dir):
    '''
    fio-plotters: plot storage IO benchmarks
    this tool plots storage benchmarks of:\n
    1. bandwidth\n
    2. iops\n
    3. average latency\n
    the tool reads input fio-bm jsons, extracts values corresponding to the
    benchmark type, and creates the resulting plots.
    '''
    if not output_dir:
        output_dir = os.getcwd()

    fio_input_files = []
    for fio_input_dir in fio_input_dirs:
        fio_input_paths = Path(fio_input_dir).rglob('*.json')
        for f_p in fio_input_paths:
            fio_input_files.append(str(f_p))

    df = json_parser.parse(fio_input_files)

    # print(df)

    plotter.plot(df, output_dir)


if __name__ == '__main__':
    cli()
