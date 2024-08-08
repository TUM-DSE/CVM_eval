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
# LINUX_COMMIT := "0dd3ee31125508cd67f7e7172247f05b7fd1753a" # v6.7
LINUX_COMMIT := "e8f897f4afef0031fe618a8e94127a0934896aba" # v6.8

BRIDGE_NAME := "virbr_cvm"
TAP_NAME := "tap_cvm"
MTAP_NAME := "mtap_cvm"

default:
    @just --choose

# ------------------------------
# QEMU commands
# e.g., just smp=16 start-vm-disk
# note: setting values (`smp=16`) needs to come before the command

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
        -netdev bridge,id=en0,br={{BRIDGE_NAME}} \
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
        -netdev bridge,id=en0,br={{BRIDGE_NAME}} \
        -device virtio-net-pci,netdev=en0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0

start-vm-direct-vhost:
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
        -netdev tap,id=en0,ifname={{TAP_NAME}},script=no,downscript=no,vhost=on,queues=2 \
        -device virtio-net-pci,netdev=en0,mq=on,vectors=18 \
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
        -netdev bridge,id=en0,br={{BRIDGE_NAME}} \
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
        -netdev bridge,id=en0,br={{BRIDGE_NAME}} \
        -device virtio-net-pci,netdev=en0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0

# ------------------------------
# TDX machine
#

#TDX_QEMU := "qemu-system-x86_64"
TDX_QEMU := join(BUILD_DIR, "qemu-tdx/bin/qemu-system-x86_64")
#TDVF_FIRMWARE := "/usr/share/ovmf/OVMF.fd"
TDVF_FIRMWARE := join(BUILD_DIR, "ovmf-tdx-fd/FV/OVMF.fd")
TDSHIM := "../td-shim/target/release/final.bin"
CLOUD_HYPERVISOR := "../cloud-hypervisor/target/release/cloud-hypervisor"
TD_IMG := join(BUILD_DIR, "image/tdx-guest-ubuntu-24.04-generic.qcow2")
QUOTE_ARGS := "-device vhost-vsock-pci,guest-cid=3"

start-tdx-vm:
    {{TDX_QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35,hpet=off,kernel_irqchip=split,memory-encryption=tdx,memory-backend=ram1 \
        -enable-kvm \
        -object tdx-guest,id=tdx \
        -object memory-backend-ram,id=ram1,size={{mem}},private=on \
        -bios {{TDVF_FIRMWARE}} \
        -nographic \
        -nodefaults \
        -serial stdio \
        -device virtio-net-pci,netdev=nic0_td \
        -netdev user,id=nic0_td,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -drive file={{TD_IMG}},if=none,id=virtio-disk0 \
        -device virtio-blk-pci,drive=virtio-disk0 \
        {{QUOTE_ARGS}}

start-tdx-direct:
    {{TDX_QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -machine q35,hpet=off,kernel_irqchip=split,memory-encryption=tdx,memory-backend=ram1 \
        -enable-kvm \
        -object tdx-guest,id=tdx \
        -object memory-backend-ram,id=ram1,size={{mem}},private=on \
        -kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        -append "root=/dev/vda console=hvc0" \
        -bios {{TDVF_FIRMWARE}} \
        -nographic \
        -nodefaults \
        -device virtio-net-pci,netdev=nic0_td \
        -netdev user,id=nic0_td,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -drive file={{GUEST_FS}},if=none,id=virtio-disk0 \
        -device virtio-blk-pci,drive=virtio-disk0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0 \
        {{QUOTE_ARGS}}

start-ch:
   {{CLOUD_HYPERVISOR}} \
        --kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        --cmdline "console=hvc0 root=/dev/vda rw" \
        --cpus boot={{smp}} \
        --memory size={{mem}} \
        --disk path={{GUEST_FS}} 

start-ch-tdvf:
   {{CLOUD_HYPERVISOR}} \
        --platform tdx=on \
        --firmware {{TDVF_FIRMWARE}} \
        --kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        --cmdline "console=hvc0 root=/dev/vda rw" \
        --cpus boot={{smp}} \
        --memory size={{mem}} \
        --disk path={{GUEST_FS}} 

start-ch-tdshim:
   {{CLOUD_HYPERVISOR}} \
        --platform tdx=on \
        --firmware {{TDSHIM}} \
        --kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        --cmdline "console=hvc0 root=/dev/vda rw" \
        --cpus boot={{smp}} \
        --memory size={{mem}} \
        --disk path={{GUEST_FS}} 

start-intel-direct:
    {{TDX_QEMU}} \
        -cpu host \
        -smp {{smp}} \
        -m {{mem}} \
        -enable-kvm \
        -kernel {{LINUX_DIR}}/arch/x86/boot/bzImage \
        -append "root=/dev/vda console=hvc0" \
        -bios {{TDVF_FIRMWARE}} \
        -nographic \
        -nodefaults \
        -device virtio-net-pci,netdev=nic0_td \
        -netdev user,id=nic0_td,hostfwd=tcp::{{SSH_PORT}}-:22 \
        -drive file={{GUEST_FS}},if=none,id=virtio-disk0 \
        -device virtio-blk-pci,drive=virtio-disk0 \
        -serial null \
        -device virtio-serial \
        -chardev stdio,mux=on,id=char0,signal=off \
        -mon chardev=char0,mode=readline \
        -device virtconsole,chardev=char0,id=vc0,nr=0

# ------------------------------
# Utility commands

ssh command="":
    chmod 600 ./nix/ssh_key
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
    patch -d {{ LINUX_DIR }} -p1 < {{ PROJECT_ROOT }}/nix/patches/linux_tdx_allow_user_io.patch
    patch -d {{ LINUX_DIR }} -p1 < {{ PROJECT_ROOT }}/nix/patches/linux_tdx_export_hypercall.patch

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

# kernel configuration tested with v6.8
configure-linux debug="":
    #!/usr/bin/env bash
    set -xeuo pipefail
    if [[ ! -f {{ LINUX_DIR }}/.config ]]; then
      cd {{ LINUX_DIR }}
      {{ KERNEL_SHELL }} "make defconfig kvm_guest.config"
      {{ KERNEL_SHELL }} "scripts/config \
         --enable AMD_MEM_ENCRYPT \
         --disable AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT \
         --enable VIRT_DRIVERS \
         --enable SEV_GUEST"
      if [[ "{{ debug }}" = "debug" ]]; then
        {{ KERNEL_SHELL }} "scripts/config \
           --enable CONFIG_IKCONFIG \
           --enable CONFIG_IKCONFIG_PROC \
           --enable KPROBES \
           --enable KPROBES_ON_FTRACE \
           --enable KPROBE_EVENTS \
           --enable DYNAMIC_FTRACE \
           --enable DYNAMIC_FTRACE_WITH_REGS \
           --enable DYNAMIC_FTRACE_WITH_ARGS \
           --enable DYNAMIC_EVENTS \
           --enable BPF \
           --enable BPF_SYSCALL \
           --enable BPF_EVENTS \
           --enable BPF_JIT \
           --enable TRACEPOINTS \
           --enable FUNCTION_TRACER \
           --enable DEBUG_INFO \
           --enable DEBUG_INFO_BTF \
           --enable IKCONFIG \
           --enable IKCONFIG_PROC \
           --enable IKHEADERS"
        fi
    fi

# kernel configuration tested with v6.8
configure-linux-tdx:
    #!/usr/bin/env bash
    set -xeuo pipefail
    if [[ ! -f {{ LINUX_DIR }}/.config ]]; then
      cd {{ LINUX_DIR }}
      {{ KERNEL_SHELL }} "make defconfig kvm_guest.config"
      {{ KERNEL_SHELL }} "scripts/config \
         --enable X86_X2APIC \
         --enable INTEL_TDX_GUEST \
         --enable VIRT_DRIVERS \
         --enable CONFIGFS_FS \
         --enable TSM_REPORTS \
         --enable TDX_GUEST_DRIVER"
      # for debug
      #{{ KERNEL_SHELL }} "scripts/config \
      #   --enable KPROBES \
      #   --enable KPROBES_ON_FTRACE \
      #   --enable BPF \
      #   --enable BPF_SYSCALL \
      #   --enable BPF_EVENTS \
      #   --enable BPF_JIT \
      #   --enable TRACEPOINTS \
      #   --enable DEBUG_INFO_BTF \
      #   --enable IKCONFIG \
      #   --enable IKCONFIG_PROC \
      #   --enable IKHEADERS"
    fi

menuconfig:
    #!/usr/bin/env bash
    cd {{ LINUX_DIR }}
    {{ KERNEL_SHELL }} "make menuconfig"

build-linux:
    #!/usr/bin/env bash
    set -xeu
    cd {{ LINUX_DIR }}
    yes "" | {{ KERNEL_SHELL }} "make KCFLAGS=-Wno-error=missing-prototypes -C {{ LINUX_DIR }} -j$(nproc)"

build-perf:
    #!/usr/bin/env bash
    set -xeu
    cd {{ LINUX_DIR }}/tools/perf
    {{ KERNEL_SHELL }} "NIX_CFLAGS_COMPILE='-idirafter /usr/include -O2' make -j$(nproc)"
    mkdir -p guest-tools
    cp {{ LINUX_DIR }}/tools/perf/perf guest-tools

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
    ip a s {{BRIDGE_NAME}} >/dev/null 2>&1
    if [ $? ]; then
        sudo brctl addbr {{BRIDGE_NAME}}
        sudo ip a a 172.44.0.1/24 dev {{BRIDGE_NAME}}
        sudo ip l set dev {{BRIDGE_NAME}} up
    fi

setup_tap:
    sudo ip tuntap add {{TAP_NAME}} mode tap
    sudo ip link set {{TAP_NAME}} master {{BRIDGE_NAME}}
    sudo ip link set {{TAP_NAME}} up
    sudo ip tuntap add {{MTAP_NAME}} mode tap multi_queue
    sudo ip link set {{MTAP_NAME}} master {{BRIDGE_NAME}}
    sudo ip link set {{MTAP_NAME}} up

remove_bridge:
    #!/usr/bin/env bash
    sudo ip link set dev {{TAP_NAME}} down
    sudo ip link del {{TAP_NAME}}
    sudo ip link set dev {{MTAP_NAME}} down
    sudo ip link del {{MTAP_NAME}}
    sudo ip link set dev {{BRIDGE_NAME}} down
    sudo brctl delbr {{BRIDGE_NAME}}

# These commands should show info on virbr0
show_bridge_status:
    #!/usr/bin/env bash
    set -x
    ip a show dev {{BRIDGE_NAME}}
    brctl show
    networkctl

# ------------------------------
# trace
trace name duration="20" interval="1":
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    bash {{PROJECT_ROOT}}/trace/all.sh {{name}} {{duration}} {{interval}} $DATE &
    just ssh "bash /share/trace/all.sh {{name}} {{duration}} {{interval}} $DATE"
    wait $(jobs -p)
    sleep 1
    just flamegraph {{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/host/perf.data {{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/host/perf.svg
    just flamegraph-guest {{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/guest/perf.data {{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/guest/perf.svg

mpstat name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/host
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/mpstat.sh {{name}} &
    OUTDIR=/share/trace-result/{{name}}/$DATE/guest
    just ssh "OUTDIR=$OUTDIR bash /share/trace/mpstat.sh"
    wait $(jobs -p)

vmstat name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE/host
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/vmstat.sh {{name}}
    OUTDIR=/share/trace-result/{{name}}/$DATE/guest
    just ssh "OUTDIR=$OUTDIR bash /share/trace/vmstat.sh"

trace-host name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/all.sh

perf-host name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/perf.sh

stat-host name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/stat.sh {{name}}

mpstat-host name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR={{PROJECT_ROOT}}/trace-result/{{name}}/$DATE
    export OUTDIR
    bash {{PROJECT_ROOT}}/trace/mpstat.sh {{name}}

trace-guest name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR=/share/trace-result/{{name}}/$DATE
    just ssh "OUTDIR=$OUTDIR bash /share/trace/all.sh"

perf-guest name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR=/share/trace-result/{{name}}/$DATE
    just ssh "OUTDIR=$OUTDIR bash /share/trace/perf.sh"

stat-guest name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR=/share/trace-result/{{name}}/$DATE
    just ssh "OUTDIR=$OUTDIR bash /share/trace/stat.sh"

mpstat-guest name:
    #!/usr/bin/env bash
    DATE=$(date '+%Y-%m-%d-%H-%M-%S')
    OUTDIR=/share/trace-result/{{name}}/$DATE
    just ssh "OUTDIR=$OUTDIR bash /share/trace/mpstat.sh"

flamegraph in="perf.data" out="a.svg":
    #!/usr/bin/env bash
    TMP=$(mktemp -p /tmp)
    trap 'rm -f $TMP' EXIT
    perf script -i {{in}} | {{PROJECT_ROOT}}/../FlameGraph/stackcollapse-perf.pl > $TMP
    {{PROJECT_ROOT}}/../FlameGraph/flamegraph.pl $TMP > {{out}}

flamegraph-guest in="perf.data" out="a.svg":
    #!/usr/bin/env bash
    TMP=$(mktemp -p /tmp)
    trap 'rm -f $TMP' EXIT
    perf script -k {{LINUX_DIR}}/vmlinux -i {{in}} | {{PROJECT_ROOT}}/../FlameGraph/stackcollapse-perf.pl > $TMP
    {{PROJECT_ROOT}}/../FlameGraph/flamegraph.pl $TMP > {{out}}

# command for the guest (run in the guest)
perf-record sec="10" out="perf.data":
   {{KERNEL_SHELL}} "{{PROJECT_ROOT}}/guest-tools/perf record --output {{out}} -a -g -- sleep {{sec}}"

perf-report in="perf.data" out="report.txt":
   {{KERNEL_SHELL}} "{{PROJECT_ROOT}}/guest-tools/perf report -i {{in}} -k {{PROJECT_ROOT}}/guest-tools/vmlinux --no-children > {{out}}"
