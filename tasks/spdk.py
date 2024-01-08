#!/usr/bin/env python3
import os
import time
from typing import Any

from common import info_print, print_and_run, print_and_sudo, warn_nvm_use, err_print, warn_print

from invoke import task

# constants
RPC_BIN = "PYTHONPATH=$PYTHONPATH:/nix/store/wwqv98k9bysyz05772vwr1jpgi61azz8-spdk-23.09/bin rpc.py"
SETUP_BIN = "spdk-setup.sh"
VHOST_BIN = "vhost"
VHOST_SOCK = "/var/tmp"
SPDK_SOCK = "/var/tmp/spdk.sock"

VHOST_CONTROLLER_NAME = "vhost.1"
VIRTIO_BLK_CONTROLLER_NAME = "VirtioBlk1"
NVME_CONTROLLER_NAME = "Nvme1"

# helpers
def _select_ssd_pci_addr(c: Any):
    """
    Select NVMe SSD PCI address
    """
    ssd_pci_address: str = ""

    status_out_list: list[str] = print_and_sudo(c, f"{SETUP_BIN} status").stdout.splitlines()

    for line in status_out_list:
        if "vfio-pci" in line:
            if ssd_pci_address:
                warn_print(f"multiple nvme devices found. using first ({ssd_pci_address})")
                continue
            ssd_pci_address = line.split()[1]

    if not ssd_pci_address:
        err_print("no vfio-pci-bound nvme ssd found. Consider running setup_vhost_target first.")
        exit(1)
            
    # warn here as we then use this SSD
    warn_nvm_use(ssd_pci_address)
    return ssd_pci_address

def _clean_spdk_setup(c):
    print_and_sudo(c, f"CLEAR_HUGE=yes {SETUP_BIN} cleanup")
    time.sleep(2)
    print_and_sudo(c, f"{SETUP_BIN} reset")

def _bind_ssd_and_alloc_hugepages(c, huge_mem=8192):
    # get nvme pci address via nvme driver before binding
    print_and_sudo(c, f"HUGEMEM={huge_mem} {SETUP_BIN}")


# only for dev purposes
# NOT for benchmarking
def setup_vhost_blk_virtio_malloc(c: Any, cpu_mask="0x1"):
    print_and_sudo(c, f"{RPC_BIN} bdev_malloc_create 64 512 -b Malloc0")
    print_and_sudo(c, f"{RPC_BIN} vhost_create_blk_controller --cpumask {cpu_mask} {VHOST_CONTROLLER_NAME} Malloc0")

# assumes VHOST_SOCK is already setup
# see https://github.com/frankfanslc/spdk/blob/1c5444d623dae3b1b1ce40394488f43f47231bad/test/vhost/initiator/blockdev.sh#L74
def setup_vhost_blk_ssd(c: Any, cpu_mask="0x1"):
    # attach virtio blk controller to NVMe SSD
    # see https://spdk.io/doc/bdev.html#bdev_config_virtio_blk
    pci_addr = _select_ssd_pci_addr(c)

    # NOTE: this is the NVMe setup; it does not seem to work w/ poll_queues
    dev_name: str = print_and_sudo(c, f"{RPC_BIN} bdev_nvme_attach_controller --name {NVME_CONTROLLER_NAME} --trtype PCIe --traddr {pci_addr}").stdout.strip()
    # can't connect this setup to nvme ssd
    # dev_name: str = print_and_sudo(c, f"{RPC_BIN} bdev_virtio_attach_controller --dev-type=blk --trtype pci --traddr {pci_addr} {VIRTIO_BLK_CONTROLLER_NAME}").stdout.strip()
    print_and_sudo(c, f"{RPC_BIN} vhost_create_blk_controller --cpumask {cpu_mask} {VHOST_CONTROLLER_NAME} {dev_name}")


@task
def clean_spdk_setup(c):
    """
    Clean up spdk setup
    """
    _clean_spdk_setup(c)

@task(help={
    "huge_mem": "Amount of hugepage mem to allocate (in MB)",
    "cpu_mask": "CPU mask to use for vhost target"
    })
def setup_vhost_target(c, huge_mem=8192, cpu_mask="0x3"):
    """
    Setup vhost target
    """
    _bind_ssd_and_alloc_hugepages(c, huge_mem)
    info_print("starting vhost target- leave running, binding to this TTY")
    print_and_sudo(c, f"{VHOST_BIN} -S {VHOST_SOCK} -m {cpu_mask}")
    # wait until /var/tmp/spdk.sock exists in python
    timeout: int = 10
    while not os.path.exists(SPDK_SOCK):
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            msg = f"Timeout waiting for {SPDK_SOCK} to exist"
            err_print(msg)
            raise Exception(msg)



# helpful links:
# - https://github.com/finallyjustice/sample/blob/a4eac8976aa3af0ccc762f91c94caacb577af74d/spdk/vhost-user.txt#L61
@task()
def setup_vhost_blk_backend(c: Any) -> None:
    """
    Setup virtio-blk spdk backend for vhost target
    """
    setup_vhost_blk_ssd(c)
    # print_and_run(c, f""{RPC_BIN} bdev_virtio_attach_controller -b Nvme0 -u 0")

@task
def test_spdk(c) -> None:
    if print_and_run(c, no_check=True, cmd=f"nc -z localhost 2222", hide=True).failed:
        exit(1)
        
