#!/usr/bin/env python3

from invoke import Collection

from . import utils, build, vm
from . import plot_phoronix_memory, plot_application, plot_network
from . import plot_boottime, plot_vmexit

ns = Collection()
ns.add_collection(Collection.from_module(utils))
ns.add_collection(Collection.from_module(build))
ns.add_collection(Collection.from_module(vm))
ns.add_collection(Collection.from_module(plot_phoronix_memory), "phoronix")
ns.add_collection(Collection.from_module(plot_application), "app")
ns.add_collection(Collection.from_module(plot_network), "network")
ns.add_collection(Collection.from_module(plot_boottime), "boottime")
ns.add_collection(Collection.from_module(plot_vmexit), "vmexit")
