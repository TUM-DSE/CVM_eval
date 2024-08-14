#!/usr/bin/env bash

action=$1
remote=false
repeat=${2:-1}

for i in $(seq 1 $repeat); do
    for type in amd; do
        inv vm.start --type ${type} --virtio-nic --action=${action}
        inv vm.start --type ${type} --virtio-nic --action=${action} --virtio-nic-vhost
    done

    #swiotlb enabled for normal vm
    inv vm.start --virtio-nic --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force

    # #idle poll enabled for cvm
    # inv vm.start --type snp --virtio-nic --action=${action} --extra-cmdline idle=poll --name-extra -poll

    # #halt poll enabled for cvm
    # inv vm.start --type snp --virtio-nic --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
done
