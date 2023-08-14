#!/bin/bash

set -Eeo pipefail

# ./usr/local/bin/qemu-system-x86_64 \
./usr/qemu/usr/bin/qemu-system-x86_64 \
    -enable-kvm \
    -cpu EPYC-v4,host-phys-bits=true \
    -smp 16 \
    -m 16G \
    -machine type=q35 \
    -drive if=pflash,format=raw,unit=0,file=./OVMF_files/OVMF_CODE_nosev.fd,readonly=on \
    -drive if=pflash,format=raw,unit=1,file=./OVMF_files/OVMF_VARS_nosev.fd \
    -drive file=cloud-config-nosev.iso,media=cdrom,index=0 \
    -drive file=nosev.img,if=none,id=disk0,format=raw \
    -object memory-backend-file,id=mem,size=1G,mem-path=/dev/hugepages,share=on \
    -numa node,memdev=mem \
    -drive file=guest_os_image.qcow2,if=none,id=disk \
    -device ide-hd,drive=disk,bootindex=0 \
    -chardev socket,id=char1,path=/var/tmp/vhost.1
-device vhost-user-blk-pci,id=blk0,chardev=char1
    -nographic \
    -device virtio-net-pci,netdev=net0 \
    -netdev user,id=net0,hostfwd=tcp::2223-:22

