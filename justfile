# vim: set ft=make et :

PROJECT_ROOT := justfile_directory()
BUILD_DIR := join(PROJECT_ROOT, "build")
QEMU_SNP := join(BUILD_DIR, "qemu-amd-sev-snp/bin/qemu-system-x86_64")
OVMF_SNP := join(BUILD_DIR, "ovmf-amd-sev-snp-fd/FV/OVMF.fd")
SNP_IMAGE := join(BUILD_DIR, "image/snp-guest-image.qcow2")
NORMAL_IMAGE := join(BUILD_DIR, "image/normal-guest-image.qcow2")
SSH_PORT := "2225"

default:
    @just --choose

start-vm-disk:
    sudo {{QEMU_SNP}} \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{SNP_IMAGE}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -drive if=pflash,format=raw,unit=0,file={{OVMF_SNP}},readonly=on

start-snp-disk:
    sudo {{QEMU_SNP}} \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0 \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{SNP_IMAGE}} \
        -device virtio-blk-pci,drive=q2 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -drive if=pflash,format=raw,unit=0,file={{OVMF_SNP}},readonly=on

ssh port="2225":
    ssh -i nix/ssh_key -o "StrictHostKeyChecking no" -p {{ port }} root@localhost

