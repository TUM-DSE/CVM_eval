
size="medium"

inv vm.start --virtio-nic --action $1 --repeat $2 --size $size
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --remote
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost --remote

inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --type snp
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --remote --type snp
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost --type snp
inv vm.start --virtio-nic --action $1 --repeat $2 --size $size --virtio-nic-vhost --remote --type snp

