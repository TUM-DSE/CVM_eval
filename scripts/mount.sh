#!/bin/bash

# mount virtio-9p and virtio-blk (if any) in the guest
# useful for non-nix-generated images

mkdir -p /share
mount -t 9p -o trans=virtio,version=9p2000.L share /share

if [ -e /dev/vdb ]; then
    mkdir -p /mnt
    mount /dev/vdb /mnt
fi
