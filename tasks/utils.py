#!/usr/bin/env python3

from pathlib import Path

from invoke import task

import config


@task
def show_config(ctx):
    print(f'SCRIPT_ROOT: {config.SCRIPT_ROOT}')
    print(f'PROJECT_ROOT: {config.PROJECT_ROOT}')
    print(f'BUILD_DIR: {config.BUILD_DIR}')
