# TODO: transform to nix
# SSD set up and preconditioning as in:
# https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf

# resource locations
## dirs
proot     := justfile_directory()
build     := join(proot, "build")
vm_build  := join(build, "vm")

## build resources
# img same for native as SEV
# SEV changes already merged upstream
# different qcow2 images
qcow2                  := "nixos.qcow2"
img_native_dir_ro      := join(vm_build, "img-native-ro")
img_amd_sev_snp_dir_ro := join(vm_build, "img-sev-ro")
img_native_ro          := join(img_native_dir_ro, qcow2)
img_amd_sev_snp_ro     := join(img_amd_sev_snp_dir_ro, qcow2)
img_native_dir         := join(vm_build, "img-native")
img_amd_sev_snp_dir    := join(vm_build, "img-sev")
img_native             := join(img_native_dir, qcow2)
img_amd_sev_snp        := join(img_amd_sev_snp_dir, qcow2)
ovmf_ro                := join(vm_build, "OVMF-ro")
ovmf_ro_fd             := join(vm_build, "OVMF-ro-fd")
native_ovmf            := join(vm_build, "native", "OVMF")
sev_ovmf               := join(vm_build, "sev", "OVMF")
uefi_bios_ro           := join(ovmf_ro_fd, "FV", "OVMF.fd")
uefi_bios_code_ro      := join(ovmf_ro_fd, "FV", "OVMF_CODE.fd")
uefi_bios_vars_ro      := join(ovmf_ro_fd, "FV", "OVMF_VARS.fd")
native_uefi_bios_code  := join(native_ovmf, "FV", "OVMF_CODE.fd")
sev_uefi_bios_code     := join(sev_ovmf, "FV", "OVMF_CODE.fd")
native_uefi_bios_vars  := join(native_ovmf, "FV", "OVMF_VARS.fd")
sev_uefi_bios_vars     := join(sev_ovmf, "FV", "OVMF_VARS.fd")
# uefi_bios              := join(ovmf, "FV", "OVMF.fd")


# nix identifiers
## recipes
this_dir             := "."
nix_img              := join(this_dir, "#guest-image")
nix_ovmf_amd_sev_snp := join(this_dir, "#ovmf-amd-sev-snp")

# commands
update_nix_kernel_src := "nix flake lock --update-input kernelSrc"


default:
    @just --choose


help:
    just --list

poll-benchmark port="2222" filename="native-result.log" sleep="1200": numa-warning
    echo "polling {{port}} ; saving to {{filename}} ; waiting {{sleep}} before polling"
    # waiting for 10 jobs * 120 secs
    sleep {{sleep}}
    while ! scp -P {{port}} -q  -o StrictHostKeyChecking=no -i ./nix/ssh_key root@localhost:/mnt/bm-result.log ./logs/{{filename}} &>/dev/null ; do \
        echo "polling for completed log..." ; \
        sleep 10 ; \
    done


start-native-vm-virtio-blk EXTRA_CMDLINE="virtio_blk.cvm_io_driver_name=virtio2" nvme="/dev/nvme1n1":
    # sudo for disk access
    # device: /dev/nvme1n1 ( Samsung SSD PM173X )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31
    # cat nvme1n1 /sys/class/nvme/nvme1/device/numa_node : 0
    # --> 4-8 on same node as NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{native_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{native_uefi_bios_vars}} \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2 \
        -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={{nvme}} \
        -device virtio-blk,drive=q1


start-native-vm-virtio-blk-poll nvme="/dev/nvme1n1":
    # sudo for disk access
    # device: /dev/nvme1n1 ( Samsung SSD PM173X )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31
    # cat nvme1n1 /sys/class/nvme/nvme1/device/numa_node : 0
    # --> 4-8 on same node as NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{native_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{native_uefi_bios_vars}} \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2 \
        -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={{nvme}} \
        -device virtio-blk,drive=q1


start-native-vm-io_uring nvme="/dev/nvme1n1":
    # sudo for disk access
    # device: /dev/nvme1n1 ( Samsung SSD PM173X )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31
    # cat nvme1n1 /sys/class/nvme/nvme1/device/numa_node : 0
    # --> 4-8 on same node as NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{native_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{native_uefi_bios_vars}} \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2 \
        -drive aio=io_uring,format=raw,file.driver=host_device,cache=none,file.filename={{nvme}}



start-native-vm-spdk-vhost-user-blk:
    # sudo for disk access
    # device: /dev/nvme1n1 ( Samsung SSD PM173X )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31
    # cat nvme1n1 /sys/class/nvme/nvme1/device/numa_node : 0
    # --> 4-8 on same node as NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{native_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{native_uefi_bios_vars}} \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -object memory-backend-file,id=mem,size=16G,mem-path=/dev/hugepages,share=on \
        -numa node,memdev=mem \
        -chardev socket,id=char1,path=/var/tmp/vhost.1 \
        -device vhost-user-blk-pci,id=blk0,chardev=char1

start-native-vm-spdk-vfio-user-nvme:
    # sudo for disk access
    # device: /dev/nvme1n1 ( Samsung SSD PM173X )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31
    # cat nvme1n1 /sys/class/nvme/nvme1/device/numa_node : 0
    # --> 4-8 on same node as NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{native_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{native_uefi_bios_vars}} \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -object memory-backend-file,id=mem,size=4G,mem-path=/dev/hugepages,share=on,prealloc=yes \
        -numa node,memdev=mem \
        -device vfio-user-pci,socket=/var/run/cntrl



start-sev-vm-virtio-blk nvme="/dev/nvme1n1":
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_amd_sev_snp}} \
        -device virtio-blk-pci,drive=q2 \
        -netdev user,id=net0,hostfwd=tcp::2223-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{sev_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{sev_uefi_bios_vars}} \
        -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={{nvme}} \
        -device virtio-blk,drive=q1


start-sev-vm-io_uring nvme="/dev/nvme1n1":
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_amd_sev_snp}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -netdev user,id=net0,hostfwd=tcp::2223-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{sev_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{sev_uefi_bios_vars}} \
        -drive aio=io_uring,format=raw,file.driver=host_device,cache=none,file.filename={{nvme}}


start-sev-vm-spdk:
    {{ error("doesn't work out-of-the-box") }}
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_amd_sev_snp}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -netdev user,id=net0,hostfwd=tcp::2223-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{sev_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{sev_uefi_bios_vars}} \
        -object memory-backend-file,id=mem,size=16G,mem-path=/dev/hugepages,share=on \
        -numa node,memdev=mem \
        -chardev socket,id=char1,path=/var/tmp/vhost.1 \
        -device vhost-user-blk-pci,id=blk0,chardev=char1


start-sev-vm:
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu EPYC-v4,host-phys-bits=true \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_amd_sev_snp}} \
        -device virtio-blk-pci,drive=q2,bootindex=0 \
        -netdev user,id=net0,hostfwd=tcp::2223-:22 \
        -device virtio-net-pci,netdev=net0 \
        -drive if=pflash,format=raw,unit=0,file={{sev_uefi_bios_code}},readonly=on \
        -drive if=pflash,format=raw,unit=1,file={{sev_uefi_bios_vars}}

## VM BUILD

img-build: build-linux
    # TODO: differentiate between prebuilt and nixbuilt
    {{update_nix_kernel_src}}
    mkdir -p {{vm_build}}
    # vm images
    nix build -L -o {{img_native_dir_ro}} {{nix_img}}
    nix build -L -o {{img_amd_sev_snp_dir_ro}} {{nix_img}}
    install -D -m644 {{img_native_ro}} {{img_native}}
    install -D -m644 {{img_amd_sev_snp_ro}} {{img_amd_sev_snp}}

ovmf-build:
    mkdir -p {{vm_build}}
    nix build -L -o {{ovmf_ro}} {{nix_ovmf_amd_sev_snp}}
    install -D -m644 {{uefi_bios_vars_ro}} {{native_uefi_bios_vars}}
    install -D -m644 {{uefi_bios_code_ro}} {{native_uefi_bios_code}}
    install -D -m644 {{uefi_bios_vars_ro}} {{sev_uefi_bios_vars}}
    install -D -m644 {{uefi_bios_code_ro}} {{sev_uefi_bios_code}}


vm-build: img-build ovmf-build
    # resize
    qemu-img resize {{img_native}} +2g
    # qemu-img resize {{img_amd_sev_snp}} +2g
    # ovmf

## SSD setup
init-spdk: 
    sudo HUGEMEM=32768 spdk-setup.sh

precondition-ssd-standard:
    echo "NOTE: preconditioning only required when a. inconsistent results b. SSD is new / not yet reached steady state"
    # NOTE: when to perform:
    # 1. new SSD -> reach steady state
    # 2. inconsistent results
    # source: https://www.youtube.com/watch?v=tkGE3pq5eIU&list=PLj-81kG3zG5ZIE-4CvqsvlFEHoOoWRIHZ&index=9
    # hugepages required to run any spdk applications
    # regardless of whether we need hugepages
    # sudo spdk-setup.sh
    # Vislor SSD already formatted;
    # to format own SSD, use `nvme_manage` ; follow steps in:
    # https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf
    #
    # ensure LBA has been written to by filling up span of drive 2 times w/
    # sequential writes (1.6TB -> 1600000000000B ; 1.6TB*2 -> 3200000000000
    # if fails: you may need to init hugepages via `just init-spdk`
    sudo perf -q 32 -s 32768 -o 3200000000000 -t 1200 -w write -c 0x1 -r 'trtype:PCIe traddr:0000:64:00.00'


precondition-ssd-randwrite:
    # if 4KB rand writes ( which we do ):
    # in talk: 90 min writes ; they needed 10min / 800 GB -> 90min / 7200GB (factor 9)
    # our case: 9*1.6TB -> 14.4TB -> 14400000000000B (per doesn't use time anymore; only size
    # if fails: you may need to init hugepages via `just init-spdk`
    sudo perf -q 32 -s 4096 -w randwrite -o 14400000000000 -t 5400 -c 0x1 -r 'trtype:PCIe traddr:0000:64:00.00'


numa-warning:
    echo "Please ensure your NUMA config is correct; else, inconsistent results"
    echo "Displaying lspci bus addr + NUMA nodes; please check manually"
    # or look manually via e.g. cat /sys/class/nvme/nvme1/device/numa_node
    lspci | grep -i Non
    lscpu | grep NUMA


spdk-setup:
    sudo nix develop
    # bind ssd to vfio driver
    spdk-setup.sh
    vhost -S /var/tmp -m0x3 2>&1 | tee logs/vhost.log &
    rpc.py bdev_nvme_attach_controller -b NVMe1 -t PCIe -a 64:00.0
    rpc.py vhost_create_blk_controller --cpumask 0x1 vhost.1 NVMe1n1


clean:
    rm -rf {{vm_build}}



## DEBUG UTILS
kernel_shell := "nix-shell '<nixpkgs>' -A linux.dev --run"
linux_dir := proot + "/src/linux"
nix_results := justfile_directory() + "/.git/nix-results/" + rev
rev := `nix eval --raw .#lib.nixpkgsRev`
qemu_ssh_port := "2222"
qemu_sev_ssh_port := "2223"

# Build a disk image
image NAME="nixos" PATH="/nixos.img":
    #!/usr/bin/env bash
    set -eux -o pipefail
    if [[ nix/{{ NAME }}-image.nix -nt {{ linux_dir }}/{{ NAME }}.ext4 ]] \
       || [[ flake.lock -nt {{ linux_dir }}/{{ NAME }}.ext4 ]]; then
       nix build --out-link {{ nix_results }}/{{ NAME }}-image/ --builders '' .#{{ NAME }}-image
       install -D -m600 "{{ nix_results }}/{{ NAME }}-image{{ PATH }}" {{ linux_dir }}/{{ NAME }}.ext4
    fi

# Build kernel-less disk image for NixOS
nixos-image: image

configure-linux:
    #!/usr/bin/env bash
    cd {{ linux_dir }} && \
    {{ kernel_shell }} "make defconfig -j$(nproc)" && \
    {{ kernel_shell }} "scripts/config \
      --enable GDB_SCRIPTS \
      --enable CVM_IO \
      --enable DEBUG_INFO \
      --enable BPF \
      --enable BPF_SYSCALL \
      --enable BPF_JIT \
      --enable HAVE_EBPF_JIT \
      --enable BPF_EVENTS \
      --enable FTRACE_SYSCALLS \
      --enable FUNCTION_TRACER \
      --enable HAVE_DYNAMIC_FTRACE \
      --enable DYNAMIC_FTRACE \
      --enable HAVE_KPROBES \
      --enable KPROBES \
      --enable KPROBE_EVENTS \
      --enable ARCH_SUPPORTS_UPROBES \
      --enable UPROBES \
      --enable UPROBE_EVENTS \
      --enable DEBUG_FS \
      --enable DEBUG \
      --enable DEBUG_DRIVER \
      --enable DM_CRYPT \
      --enable CRYPTO_XTS" # --enable KGDB

build-linux:
    cd {{ linux_dir }} && yes "" | {{ kernel_shell }} 'make -j$(nproc)'

qemu-debug EXTRA_CMDLINE="virtio_blk.cvm_io_driver_name=virtio4" nvme="/dev/nvme1n1": build-linux # nixos-image
    sudo qemu-system-x86_64 \
      -kernel {{ linux_dir }}/arch/x86/boot/bzImage \
      -drive format=raw,file={{ linux_dir }}/nixos.ext4,id=mydrive,if=virtio \
      -append "root=/dev/vdb console=hvc0 nokaslr {{ EXTRA_CMDLINE }}" \
      -net nic,netdev=user.0,model=virtio \
      -netdev user,id=user.0,hostfwd=tcp:127.0.0.1:{{ qemu_ssh_port }}-:22 \
      -smp 4 \
      -m 16G \
      -cpu host \
      -virtfs local,path={{ justfile_directory() }}/..,security_model=none,mount_tag=home \
      -virtfs local,path={{ linux_dir }},security_model=none,mount_tag=linux \
      -nographic -serial null -enable-kvm \
      -device virtio-serial \
      -chardev stdio,mux=on,id=char0,signal=off \
      -mon chardev=char0,mode=readline \
      -device virtconsole,chardev=char0,id=vmsh,nr=0 \
      -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename={{nvme}} \
      -device virtio-blk,drive=q1
    # -s


attach-debug-qemu:
    # https://www.kernel.org/doc/html/latest/dev-tools/gdb-kernel-debugging.html
    # https://www.starlab.io/blog/using-gdb-to-debug-the-linux-kernel
    cd {{ linux_dir }} && {{ kernel_shell }} 'make scripts_gdb'
    cd {{ linux_dir }} && {{ kernel_shell }} 'gdb ./vmlinux -tui' # target remote :1234

ssh-into-qemu-native:
    ssh -i nix/ssh_key -o "StrictHostKeyChecking no" -p {{ qemu_ssh_port }} root@localhost

ssh-into-qemu-sev:
    ssh -i nix/ssh_key -o "StrictHostKeyChecking no" -p {{ qemu_sev_ssh_port }} root@localhost
