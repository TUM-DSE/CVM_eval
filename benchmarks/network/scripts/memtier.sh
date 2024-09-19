#!/usr/bin/env bash

remote=${1:-false}
remote_flag=""
if [[ "$remote" == "true" ]]; then
    remote_flag="--remote"
fi

for action in run-memtier-memcached run-memtier; do
    for type in intel tdx; do
        inv vm.start --type ${type} --virtio-nic $remote_flag --action=${action}
        inv vm.start --type ${type} --virtio-nic $remote_flag --action=${action} --virtio-nic-vhost
        inv vm.start --type ${type} --virtio-nic $remote_flag --action=${action} --tls
        inv vm.start --type ${type} --virtio-nic $remote_flag --action=${action} --virtio-nic-vhost --tls
    done

    #special settings with and without vhost
    #swiotlb enabled for normal vm
    inv vm.start --type intel --virtio-nic $remote_flag --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
    inv vm.start --type intel--virtio-nic $remote_flag --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force --tls
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force --tls

    #idle poll enabled for cvm
    inv vm.start --type tdx --virtio-nic $remote_flag --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type tdx --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type tdx --virtio-nic $remote_flag --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls
    inv vm.start --type tdx --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls

    #halt poll enabled for cvm
    inv vm.start --type tdx --virtio-nic $remote_flag --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type tdx --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type tdx --virtio-nic $remote_flag --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls
    inv vm.start --type tdx --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls

    #idle poll enabled for normal vm
    inv vm.start --type intel --virtio-nic $remote_flag --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll
    inv vm.start --type intel --virtio-nic $remote_flag --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll --tls

    #halt poll enabled for normal vm
    inv vm.start --type intel --virtio-nic $remote_flag --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
    inv vm.start --type intel --virtio-nic $remote_flag --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls
    inv vm.start --type intel --virtio-nic $remote_flag --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll --tls
done
