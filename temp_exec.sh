#!/usr/bin/env bash
sudo qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/OVMF-rw/OVMF_CODE.fd,readonly=on \
        -drive if=pflash,format=raw,unit=1,file=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/OVMF-rw/OVMF_VARS.fd \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/img-rw/nixos.qcow2 \
        -device virtio-blk-pci,drive=q2 \
        -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename=/dev/nvme1n1 \
        -device virtio-blk,drive=q1

