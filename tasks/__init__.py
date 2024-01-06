#!/usr/bin/env python3

from invoke import Collection, task


import kernel, run, utils

ns = Collection()
ns.add_collection(Collection.from_module(kernel))
ns.add_collection(Collection.from_module(run))
ns.add_collection(Collection.from_module(utils))
