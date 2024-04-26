# vim: set ft=make et :

PROJECT_ROOT := justfile_directory()
BUILD_DIR := join(PROJECT_ROOT, "build")
QEMU_SNP := join(BUILD_DIR, "qemu-amd-sev-snp/bin/qemu-system-x86_64")
OVMF_SNP := join(BUILD_DIR, "ovmf-amd-sev-snp-fd/FV/OVMF.fd")
# qemu and ovmf for normal guest (use SNP version for now)
QEMU := QEMU_SNP
OVMF := OVMF_SNP
SNP_IMAGE := join(BUILD_DIR, "image/snp-guest-image.qcow2")
NORMAL_IMAGE := join(BUILD_DIR, "image/normal-guest-image.qcow2")
GUEST_FS := join(BUILD_DIR, "image/guest-fs.qcow2")
SSH_PORT := "2225"
smp := "4"
mem := "16G"

REV := `nix eval --raw .#lib.nixpkgsRev`
NIX_RESULTS := justfile_directory() + "/.git/nix-results/" + REV
KERNEL_SHELL := "$(nix build --out-link " + NIX_RESULTS + "/kernel-fhs --json " + justfile_directory() + "#kernel-deps | jq -r '.[] | .outputs | .out')/bin/linux-kernel-build"
# we use ../linux as linux kernel source directory for development
LINUX_DIR := join(PROJECT_ROOT, "../linux")
LINUX_REPO := "https://github.com/torvalds/linux"
LINUX_COMMIT := "0dd3ee31125508cd67f7e7172247f05b7fd1753a" # v6.7

default:
    @just --choose

# ------------------------------
# QEMU commands
# e.g., just smp=16 start-vm-disk
# note: setting values (`smp=16`) needs to come before the command

# bzImage: `nix build.#nixosConfigurations.normal-guest.config.boot.kernelPackages`
# initrd: copied from the guest
# initpath: obtained in the guest (`cat /proc/cmdline`)
start-vm:
    sudo {{QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -kernel ./result/bzImage \
        -initrd ./initrd \
        -append "root=/dev/vda2 console=ttyS0 init=/nix/store/019clg7m4frsp790lyj8lrsy6x666paa-nixos-system-nixos-24.05.20240412.cfd6b5f/init" \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{NORMAL_IMAGE}} \
        -device virtio-blk-pci,drive=q2 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -netdev bridge,id=en0,br=virbr0 \
        -device virtio-net-pci,netdev=en0 \
        -drive if=pflash,format=raw,unit=0,file={{OVMF}},readonly=on

start-vm-disk:
    sudo {{QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{NORMAL_IMAGE}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -netdev bridge,id=en0,br=virbr0 \
        -device virtio-net-pci,netdev=en0 \
        -drive if=pflash,format=raw,unit=0,file={{OVMF}},readonly=on

start-vm-direct:
    sudo {{QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        -append "root=/dev/vda console=hvc0" \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{GUEST_FS}} \
        -device virtio-blk-pci,drive=q2 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -drive if=pflash,format=raw,unit=0,file={{OVMF}},readonly=on \
        -netdev bridge,id=en0,br=virbr0 \
        -device virtio-net-pci,netdev=en0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0

start-snp-disk:
    sudo {{QEMU_SNP}} \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0 \
        -object memory-backend-memfd-private,id=ram1,size={{mem}},share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{SNP_IMAGE}} \
        -device virtio-blk-pci,drive=q2 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -netdev bridge,id=en0,br=virbr0 \
        -device virtio-net-pci,netdev=en0 \
        -drive if=pflash,format=raw,unit=0,file={{OVMF_SNP}},readonly=on

start-snp-direct:
    sudo {{QEMU_SNP}} \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0 \
        -object memory-backend-memfd-private,id=ram1,size={{mem}},share=true \
        -enable-kvm \
        -nographic \
        -kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        -append "root=/dev/vda console=hvc0" \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{GUEST_FS}} \
        -device virtio-blk-pci,drive=q2 \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -virtfs local,path={{PROJECT_ROOT}},security_model=none,mount_tag=share \
        -drive if=pflash,format=raw,unit=0,file={{OVMF_SNP}},readonly=on \
        -netdev bridge,id=en0,br=virbr0 \
        -device virtio-net-pci,netdev=en0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0

# ------------------------------
# Utility commands

ssh command="":
    ssh -i nix/ssh_key \
        -o StrictHostKeyChecking=no \
        -o NoHostAuthenticationForLocalhost=yes \
        -p {{ SSH_PORT }} root@localhost -- "{{ command }}"

# e.g.,
# vm to host: just scp root@localhost:/root/a .
# host to vm: just scp a root@localhost:/root
# NOTE: this assumes that the command is run from the project root
scp src="" dst="":
    scp -i {{ PROJECT_ROOT }}/nix/ssh_key \
        -o StrictHostKeyChecking=no \
        -o NoHostAuthenticationForLocalhost=yes \
        -o UserKnownHostsFile=/dev/null \
        -P {{ SSH_PORT }} \
        {{ src }} {{ dst }}

stop-qemu:
    just ssh "poweroff"

# dangerous: kill all qemu processes!
kill-qemu-force:
    sudo pkill .qemu-system-x8

# ------------------------------
# Clone and build guest linux kernel for development (the built vmilnux is used for direct boot)
# (based on VMSH)

build-linux-shell:
    {{ KERNEL_SHELL }} bash

clone-linux:
    #!/usr/bin/env bash
    set -euo pipefail

    if [[ -d {{ LINUX_DIR }} ]]; then
      echo " {{ LINUX_DIR }} already exists, skipping clone"
      exit 0
    fi

    git clone {{ LINUX_REPO }} {{ LINUX_DIR }}

    set -x
    if [[ $(git -C {{ LINUX_DIR }} rev-parse HEAD) != "{{ LINUX_COMMIT }}" ]]; then
       git -C {{ LINUX_DIR }} fetch {{ LINUX_REPO }} {{ LINUX_COMMIT }}
       git -C {{ LINUX_DIR }} checkout "{{ LINUX_COMMIT }}"
    fi

    patch -d {{ LINUX_DIR }} -p1 < {{ PROJECT_ROOT }}/nix/patches/linux_event_record.patch

# kernel configuration for SEV-SNP guest
configure-linux-old:
    #!/usr/bin/env bash
    set -xeuo pipefail
    if [[ ! -f {{ LINUX_DIR }}/.config ]]; then
      cd {{ LINUX_DIR }}
      {{ KERNEL_SHELL }} "make defconfig kvm_guest.config"
      {{ KERNEL_SHELL }} "scripts/config \
         --disable DRM \
         --disable USB \
         --disable WIRELESS \
         --disable WLAN \
         --disable SOUND \
         --disable SND \
         --disable HID \
         --disable INPUT \
         --disable NFS_FS \
         --disable ETHERNET \
         --disable NETFILTER \
         --enable DEBUG \
         --enable GDB_SCRIPTS \
         --enable DEBUG_DRIVER \
         --enable KVM \
         --enable KVM_INTEL \
         --enable KVM_AMD \
         --enable KVM_IOREGION \
         --enable BPF_SYSCALL \
         --enable CONFIG_MODVERSIONS \
         --enable IKHEADERS \
         --enable IKCONFIG_PROC \
         --enable VIRTIO_MMIO \
         --enable VIRTIO_MMIO_CMDLINE_DEVICES \
         --enable PTDUMP_CORE \
         --enable PTDUMP_DEBUGFS \
         --enable OVERLAY_FS \
         --enable SQUASHFS \
         --enable SQUASHFS_XZ \
         --enable SQUASHFS_FILE_DIRECT \
         --enable PVH \
         --disable SQUASHFS_FILE_CACHE \
         --enable SQUASHFS_DECOMP_MULTI \
         --disable SQUASHFS_DECOMP_SINGLE \
         --disable SQUASHFS_DECOMP_MULTI_PERCPU \
         --enable EXPERT \
         --enable AMD_MEM_ENCRYPT \
         --disable AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT \
         --enable KVM_AMD_SEV \
         --enable CRYPTO_DEV_CCP \
         --enable CRYPTO_DEV_CCP_DD \
         --enable SEV_GUEST \
         --enable X86_CPUID"
    fi

# kernel configuration tested with v6.7
configure-linux:
    #!/usr/bin/env bash
    set -xeuo pipefail
    if [[ ! -f {{ LINUX_DIR }}/.config ]]; then
      cd {{ LINUX_DIR }}
      {{ KERNEL_SHELL }} "make defconfig kvm_guest.config"
      {{ KERNEL_SHELL }} "scripts/config \
         --enable CONFIG_IKCONFIG \
         --enable CONFIG_IKCONFIG_PROC \
         --enable AMD_MEM_ENCRYPT \
         --disable AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT \
         --enable VIRT_DRIVERS \
         --enable SEV_GUEST"
    fi

build-linux:
    #!/usr/bin/env bash
    set -xeu
    cd {{ LINUX_DIR }}
    yes "" | {{ KERNEL_SHELL }} "make -C {{ LINUX_DIR }} -j$(nproc)"

clean-linux:
    {{ KERNEL_SHELL }} "make -C {{ LINUX_DIR }} clean"

setup-linux:
    just clone-linux
    just configure-linux
    just build-linux


# ------------------------------
# network settings

setup_bridge:
    #!/usr/bin/env bash
    ip a s virbr0 >/dev/null 2>&1
    if [ $? ]; then
        sudo brctl addbr virbr0
        sudo ip a a 172.44.0.1/24 dev virbr0
        sudo ip l set dev virbr0 up
    fi

# These commands should show info on virbr0
show_bridge_status:
    #!/usr/bin/env bash
    set -x
    ip a show dev virbr0
    brctl show
    networkctl

