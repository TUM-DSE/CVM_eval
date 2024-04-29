#!/usr/bin/env python3

from invoke import Collection

from . import utils, build, vm
from . import plot_phoronix_memory, plot_application

ns = Collection()
ns.add_collection(Collection.from_module(utils))
ns.add_collection(Collection.from_module(build))
ns.add_collection(Collection.from_module(vm))
ns.add_collection(Collection.from_module(plot_phoronix_memory), "plot")
ns.add_collection(Collection.from_module(plot_application), "plot")
