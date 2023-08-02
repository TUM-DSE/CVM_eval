import os

from plot import json_parser #, plotter

import click


@click.command()
@click.option('--fio-input',
              required=True,
              type=click.File('r'),
              multiple=True,
              help='input benchmark fio json files')
@click.option('--output-dir',
              type=click.Path(dir_okay=True, exists=True),
              help='dir to which to output plots')
def cli(
        fio_input,
        output_dir):
    '''
    fio-plotters: plot storage IO benchmarks
    this tool plots storage benchmarks of:
    1. bandwidth
    2. iops
    3. average latency
    the tool reads input fio-bm jsons, extracts values corresponding to the
    benchmark type, and creates the resulting plots.
    '''
    if not output_dir:
        output_dir = os.getcwd()

    df = json_parser.parse(fio_input)

    # plotter.plot(df, output_dir)


if __name__ == '__main__':
    cli()
