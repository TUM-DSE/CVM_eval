size="medium"
repeat=5
action="run-iperf"

if [ -n "$1" ]; then
    action+="-$1"
fi

inv vm.start --virtio-nic --action $action --repeat $repeat --size $size

# inv vm.start --virtio-nic --action "run-memtier" --repeat $repeat--size $size --remote

inv vm.start --virtio-nic --action $action --repeat $repeat --size $size --virtio-nic-vhost

# inv vm.start --virtio-nic --action $action --repeat $repeat --size $size --remote ---virtio-nic-vhost

# inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --type snp
# inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --remote --type snp
# inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost --type snp
# inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost --remote --type snp