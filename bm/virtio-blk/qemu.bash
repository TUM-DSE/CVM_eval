#!/usr/bin/env bash
# executes QEMU/KVM w/:
# - virtio-blk setup w/ direct access to device;
# -> skip filesys layers to get true virtio-blk overhead

set -euo pipefail

## from CVM Presentation DPDK Summit '23
# CPU: EPYC-v4 ; use host passthrough to avoid emu
# configure as SPDK vhost perf report:
# - 8 vcpus (-smp 4) -> pin on host (taskset)
# - 16GB RAM (-m 16G)
#
# SW:
# 
# - Kernel 6.3.0 + AMDSEV latest patch

## NOTES:
# - for cpu: possibly set `-cpu host,host-phys-bits=true` for SEV (if `host` alone does not work)
#
#
qemu-system-x86_64 \
    -cpu host \
    -smp 4 \
    -m 16G \
    -machine q35 \
    -accel kvm \
    -nographic \
    -device virtio-net-pci,netdev=net0 \
    -device virtio-blk-pci \
    -netdev user,id=net0,hostfwd=tcp::2223-:22 \

