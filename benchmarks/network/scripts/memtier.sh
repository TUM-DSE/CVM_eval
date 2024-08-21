#!/usr/bin/env bash

remote=${1:-false}

for action in run-memtier-memcached-text run-memtier-memcached run-memtier; do
    for type in amd snp; do
        inv vm.start --type ${type} --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action}
        inv vm.start --type ${type} --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --virtio-nic-vhost
        inv vm.start --type ${type} --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --tls
        inv vm.start --type ${type} --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --virtio-nic-vhost --tls
    done

    #special settings with and without vhost
    #swiotlb enabled for normal vm
    inv vm.start --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
    inv vm.start --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
    inv vm.start --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force --tls
    inv vm.start --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force --tls

    #idle poll enabled for cvm
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls

    #halt poll enabled for cvm
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls
    inv vm.start --type snp --virtio-nic $([[ $remote == true ]] && echo "--remote") --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls
done
