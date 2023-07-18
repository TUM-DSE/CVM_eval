#!/bin/bash

set -Eeo pipefail

[ ! -e kinetic-server-cloudimg-amd64.img ] && wget https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-amd64.img
mkdir -p OVMF_files

# prepare the nosev machine
qemu-img convert kinetic-server-cloudimg-amd64.img nosev.img
qemu-img resize nosev.img +20G
sudo cloud-localds cloud-config-nosev.iso config/cloud-config-nosev.yml
cp ./usr/fds/OVMF_CODE.fd ./OVMF_files/OVMF_CODE_nosev.fd
cp ./usr/fds/OVMF_VARS.fd ./OVMF_files/OVMF_VARS_nosev.fd

# prepare the sev machine
qemu-img convert kinetic-server-cloudimg-amd64.img sev.img
qemu-img resize sev.img +20G
sudo cloud-localds cloud-config-sev.iso ./config/cloud-config-sev.yml
cp ./usr/fds/OVMF_CODE.fd ./OVMF_files/OVMF_CODE_sev.fd
cp ./usr/fds/OVMF_VARS.fd ./OVMF_files/OVMF_VARS_sev.fd
