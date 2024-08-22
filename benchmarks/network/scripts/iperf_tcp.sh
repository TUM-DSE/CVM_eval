#!/usr/bin/env bash

action="run-iperf"
remote=${1:-false}

remote_flag=""
if [[ "$remote" == "true" ]]; then
    remote_flag="--remote"
fi

for type in amd snp; do
    inv vm.start $remote_flag --type ${type} --virtio-nic --virtio-nic-mq --action=${action}
    inv vm.start $remote_flag --type ${type} --virtio-nic --virtio-nic-mq --action=${action} --virtio-nic-vhost
done

#special settings with and without vhost
#swiotlb enabled for normal vm
inv vm.start $remote_flag --virtio-nic --virtio-nic-mq --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force
inv vm.start $remote_flag --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --virtio-iommu --extra-cmdline swiotlb=524288,force

#idle poll enabled for cvm
inv vm.start $remote_flag --type snp --virtio-nic --virtio-nic-mq --action=${action} --extra-cmdline idle=poll --name-extra -poll
inv vm.start $remote_flag --type snp --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --extra-cmdline idle=poll --name-extra -poll

#halt poll enabled for cvm
inv vm.start $remote_flag --type snp --virtio-nic --virtio-nic-mq --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
inv vm.start $remote_flag --type snp --virtio-nic --virtio-nic-mq --virtio-nic-vhost --action=${action} --extra-cmdline cpuidle_haltpoll.force=Y --name-extra -hpoll
