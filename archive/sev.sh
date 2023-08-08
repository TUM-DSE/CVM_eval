#!/bin/bash

set -Eeo pipefail

if [ $# -lt 1 ]; then
    echo "usage: ./sev.sh <device_type>"
    exit 1
fi

if [ "$1" == "blk" ]; then
    device_type="virtio-blk-pci,drive=disk0,id=virtblk0,num-queues=4"
elif [ "$1"=="nvme" ]; then
    device_type="nvme,serial=cafebabe,drive=disk0"
elif [ "$1"=="scsi" ]; then
    device_type="virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=true"
fi
# rm -f cloud-config-nosev.iso
# sed -i "s/- \[temp\]/- \[sudo, bash, \/run\/fio.sh, nosev, "$1"\]/" ./config/cloud-config-nosev.yml
# sudo cloud-localds cloud-config-nosev.iso config/cloud-config-nosev.yml

# ./usr/local/bin/qemu-system-x86_64 \
./usr/qemu/usr/bin/qemu-system-x86_64 \
    -enable-kvm \
    -cpu EPYC-v4,host-phys-bits=true \
    -smp 16 \
    -machine type=q35,confidential-guest-support=sev0,memory-backend=ram1,kvm-type=protected,vmport=off \
    -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
    -object sev-snp-guest,id=sev0,policy=0x30000,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
    -drive if=pflash,format=raw,unit=0,file=./OVMF_files/OVMF_CODE_sev.fd,readonly=on \
    -drive if=pflash,format=raw,unit=1,file=./OVMF_files/OVMF_VARS_sev.fd \
    -drive file=cloud-config-sev.iso,media=cdrom,index=0 \
    -drive file=sev.img,if=none,id=disk0,format=raw \
    -device $device_type \
    -nographic \
    -device virtio-net-pci,netdev=net0 \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
