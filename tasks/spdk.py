#!/usr/bin/env python3
from typing import Any

from common import print_and_sudo, warn_nvm_use

from invoke import task

# constants
NVME_BIN = "nvme"
RPC_BIN = "rpc.py"
SETUP_BIN = "spdk-setup.sh"
VHOST_BIN = "vhost"
VHOST_SOCK = "/tmp/vhost.0"

VHOST_CONTROLLER_NAME = "vhost.1"
VIRITO_BLK_CONTROLLER_NAME = "VirtioBlk1"

# global vars
glob_nvme_addr = None

# helpers
# only works if spdk has not yet bound NVMe SSD
def _select_nvme_pci_addr(c: Any, nvme_id: str = "nvme1"):
    """
    Select NVMe SSD PCI address
    """
    global glob_nvme_addr
    # select NVMe SSD PCI address
    r = print_and_sudo(c, f"{NVME_BIN} list -v --output-format=json | jq '.Devices[0].Subsystems[0].Controllers[] | select(.Controller == \"{nvme_id}\").Address'")
    glob_nvme_addr = r.stdout.replace('"', '')
    # warn here as we then use this SSD
    warn_nvm_use(nvme_id)

def _clean_spdk_setup(c):
    print_and_sudo(c, f"{SETUP_BIN} reset")
    print_and_sudo(c, f"CLEAR_HUGE=yes {SETUP_BIN} cleanup")

def _bind_ssd_and_alloc_hugepages(c, huge_mem=4096):
    # get nvme pci address via nvme driver before binding
    _select_nvme_pci_addr(c)
    print_and_sudo(c, f"HUGEMEM={huge_mem} {SETUP_BIN}")

def setup_vhost_target(c, huge_mem=4096, cpu_mask="0x3"):
    _bind_ssd_and_alloc_hugepages(c, huge_mem)
    print_and_sudo(c, f"{VHOST_BIN} -S {VHOST_SOCK} -m {cpu_mask}", asynchronous=True)

# assumes VHOST_SOCK is already setup
def setup_vhost_blk_virtio(c: Any, cpu_mask="0x1"):
    # attach virtio blk controller to NVMe SSD
    # see https://spdk.io/doc/bdev.html#bdev_config_virtio_blk
    global glob_nvme_addr
    if not glob_nvme_addr:
        raise Exception("NVMe SSD PCI address not selected")
    print_and_sudo(c, f"{RPC_BIN} bdev_virtio_attach_controller --dev-type=blk --trtype pci --traddr {glob_nvme_addr} {VIRITO_BLK_CONTROLLER_NAME}")
    print_and_sudo(f"{RPC_BIN} vhost_create_blk_controller --cpumask {cpu_mask} {VHOST_CONTROLLER_NAME} {VIRITO_BLK_CONTROLLER_NAME}")


@task
def clean_spdk_setup(c):
    """
    Clean up spdk setup
    """
    _clean_spdk_setup(c)

# helpful links:
# - https://github.com/finallyjustice/sample/blob/a4eac8976aa3af0ccc762f91c94caacb577af74d/spdk/vhost-user.txt#L61
@task(clean_spdk_setup,
      help={
    "huge_mem": "Amount of hugepages to allocate",
    "num_queues": "Number of virtqueues to create",
    "size_queue": "Queue depth of virtqueues"
    })
def setup_virtio_blk_spdk_backend(c, huge_mem=4096, num_queues=2, size_queue=512):
    """
    Setup virtio-blk spdk backend
    """
    setup_vhost_target(c, huge_mem)
    setup_vhost_blk_virtio(c)
    # print_and_run(c, f""{RPC_BIN} bdev_virtio_attach_controller -b Nvme0 -u 0")

@task
def test_spdk(c):
    _select_nvme_pci_addr(c)
