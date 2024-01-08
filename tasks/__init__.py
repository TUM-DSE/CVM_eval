#!/usr/bin/env python3

from invoke import Collection, task


import build, kernel, ovmf, run, spdk, utils

ns = Collection()
ns.add_collection(Collection.from_module(build))
ns.add_collection(Collection.from_module(kernel))
ns.add_collection(Collection.from_module(ovmf))
ns.add_collection(Collection.from_module(run))
ns.add_collection(Collection.from_module(spdk))
ns.add_collection(Collection.from_module(utils))
