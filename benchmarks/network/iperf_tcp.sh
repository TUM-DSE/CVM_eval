#!/usr/bin/env bash

action="run-iperf"
remote=false
repeat=${1:-1}

for i in $(seq 1 $repeat); do
    for type in amd snp; do
        inv vm.start --type ${type} --virtio-nic --virtio-nic-mq --action=${action}
        inv vm.start --type ${type} --virtio-nic --virtio-nic-mq --action=${action} --virtio-nic-vhost
    done

    #special settings with and without vhost
    #swiotlb enabled for normal vm
    inv vm.start --virtio-nic --virtio-nic-mq --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
    inv vm.start --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force

    #idle poll enabled for cvm
    inv vm.start --type snp --virtio-nic --virtio-nic-mq --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type snp --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll

    #halt poll enabled for cvm
    inv vm.start --type snp --virtio-nic --virtio-nic-mq --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type snp --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
done
