#!/bin/bash

set -x
set -e
set -u
set -o pipefail

SWIOTLB_OPTION=' --virtio-iommu --extra-cmdline "swiotlb=524288,force"'
POLL_OPTION=' --virtio-iommu --extra-cmdline "idle=poll" --name-extra -poll'
HALTPOLL_OPTION=' --virtio-iommu --extra-cmdline "cpuidle_haltpoll.force=Y" --name-extra -haltpoll'

VM=${VM:-amd}
CVM=${CVM:-snp}
#SIZE=small
SIZE=medium

STARTTIME=$(date +%Y%m%d-%H%M%S)

for size in $SIZE
do
    for type_ in $VM $CVM
    do
        for action in ping iperf iperf-udp
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq
        done
    done
done

for size in $SIZE
do
    for type_ in $VM
    do
        for action in ping iperf iperf-udp
        do
            for option in "$SWIOTLB_OPTION"
            do
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq $option
            done
        done
    done
done

for size in $SIZE
do
    for type_ in $CVM
    do
        for action in ping iperf iperf-udp
        do
            for option in "$POLL_OPTION" "$HALTPOLL_OPTION"
            do
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq $option
            done
        done
    done
done


ENDTIME=$(date +%Y%m%d-%H%M%S)
echo "Start time: $STARTTIME"
echo "End time: $ENDTIME"
