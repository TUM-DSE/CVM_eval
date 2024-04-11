#!/usr/bin/env python3

from invoke import Collection

from . import utils, build, vm

ns = Collection()
ns.add_collection(Collection.from_module(utils))
ns.add_collection(Collection.from_module(build))
ns.add_collection(Collection.from_module(vm))
