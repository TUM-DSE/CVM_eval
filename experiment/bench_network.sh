#!/bin/bash

set -x
set -e
set -u
set -o pipefail

VM=${VM:-amd snp}

for size in medium
do
    for type_ in $VM
    do
        for action in ping iperf iperf-udp #nginx
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq
        done
    done
done

exit

for size in medium
do
    for type_ in $VM
    do
        for action in memtier memtier-memcached
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --tls
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --virtio-nic-vhost
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" --tls --virtio-nic-vhost
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-mq
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --tls --virtio-nic-mq
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --virtio-nic-vhost --virtio-nic-mq
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-mtap="mtap_cvm" --tls --virtio-nic-vhost --virtio-nic-mq
        done
    done
done
