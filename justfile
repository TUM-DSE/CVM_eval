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

# nix identifiers
## recipes
this_dir             := "."
nix_img              := join(this_dir, "#guest-image")



default:
    @just --choose


help:
    just --list

benchmark-native-virtio-blk: start-native-vm-virtio-blk
    # waiting for 10 jobs * 120 secs
    sleep $((10 * 120))
    while ! scp -P 2222 -q -i ./nix/ssh_key root@localhost:/mnt/bm-result.log ./log/bm-result.log &>/dev/null ; do \
        echo "polling for completed log..." ; \
        sleep 10 ; \
    done

start-native-vm-virtio-blk:
    # sudo for disk access
    # device: /dev/nvme2n1 ( Samsung SSD 970 EVO Plus 1TB )
    # taskset: Liu and Liu - Virtio Devices Emulation in SPDK Based On VFIO-USE
    # vislor: NVMe SSD PM173X: 64:00.0
    # vislor: NUMA node0: CPU(s): 0-31,64-96
    # --> 4-8 on same node das NVMe SSD
    sudo taskset -c 4-8 qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35 \
        -enable-kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_native}} \
        -device virtio-blk-pci,drive=q2 \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0 \
        -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename=/dev/nvme2n1 \
        -device virtio-blk,drive=q1 &> ./logs/mylog.log &


start-sev-vm-virtio-blk:
    sudo qemu-system-x86_64 \
        -cpu host \
        -smp 4 \
        -m 16G \
        -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
        -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1 \
        -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
        -accel kvm \
        -nographic \
        -blockdev qcow2,node-name=q2,file.driver=file,file.filename={{img_amd_sev_snp}} \
        -device virtio-blk-pci,drive=q2 \
        -netdev user,id=net0,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=net0


vm-build:
    mkdir -p {{vm_build}}
    # vm images
    nix build -L -o {{img_native_dir_ro}} {{nix_img}}
    nix build -L -o {{img_amd_sev_snp_dir_ro}} {{nix_img}}
    install -D -m644 {{img_native_ro}} {{img_native}}
    install -D -m644 {{img_amd_sev_snp_ro}} {{img_amd_sev_snp}}
    # resize
    # qemu-img resize {{img_native}} +2g
    # qemu-img resize {{img_amd_sev_snp}} +2g

## SSD setup
precondition-ssd: init-spdk
    echo foo

init-spdk:
    # hugepages required to run any spdk applications
    # regardless of whether we need hugepages
    sudo spdk-setup.sh


clean:
    rm -rf {{vm_build}}
