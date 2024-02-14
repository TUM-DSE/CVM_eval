qemu-system-x86_64 \
    -cpu EPYC-v4,host-phys-bits=true \
    -enable-kvm \
    -smp 4 \
    -m 16G \
    -nographic \
    -netdev user,id=net0,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=net0 \
    -blockdev qcow2,node-name=q2,file.driver=file,file.filename=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/img-rw/nixos.qcow2 \
    -device virtio-blk-pci,drive=q2 \
    -drive if=pflash,format=raw,unit=0,file=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/OVMF-rw/OVMF_CODE.fd,readonly=on \
    -drive if=pflash,format=raw,unit=1,file=/home/robert/repos/github.com/TUM_DSE/CVM_eval/tasks/../build/vm/OVMF-rw/OVMF_VARS.fd
#    -machine q35,memory-backend=ram1,confidential-guest-support=sev0,kvm-type=protected,vmport=off \
#    -object memory-backend-memfd-private,id=ram1,size=16G,share=true \
#    -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,init-flags=0,host-data=b2l3bmNvd3FuY21wbXA \
#    -blockdev node-name=q1,driver=raw,file.driver=host_device,file.filename=/dev/nvme1n1 \
#    -device virtio-blk,drive=q1


qemu-system-x86_64 \
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

