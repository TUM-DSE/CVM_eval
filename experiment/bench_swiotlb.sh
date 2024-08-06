#!/bin/bash

set -x

VM=${VM:-amd snp}
DISKS=${DISKS:-nvme1n1}

SWIOTLB_OPTION=' --virtio-iommu --extra-cmdline "swiotlb=524288,force"'

for size in medium
do
    for type_ in $VM
    do
        for action in sqlite fio
        do
            for disk in $DISKS
            do
            inv vm.start --type ${type_} --size ${size} --virtio-blk /dev/$disk --no-warn --action="run-${action}"  --fio-job "libaio" $SWIOTLB_OPTION --name-extra $disk
            done
        done
    done
done

exit

for size in medium
do
    for type_ in $VM
    do
        for action in ping iperf iperf-udp nginx
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq $SWIOTLB_OPTION --name-extra $NAME
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq $SWIOTLB_OPTION
        done
    done
done

for size in medium
do
    for type_ in $VM
    do
        for action in memtier memtier-memcached
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --tls $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --virtio-nic-vhost $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --tls --virtio-nic-vhost $SWIOTLB_OPTION 
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --tls --virtio-nic-mq $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq $SWIOTLB_OPTION
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --tls --virtio-nic-vhost --virtio-nic-mq $SWIOTLB_OPTION
        done
    done
done

