
# prepartion
# ```
# mkfs.ext4 /dev/vdb
# mount /dev/vdb /mnt
# mkdir -p /mnt/application/unixbench
# cd /mnt/application/unixbench
# git clone https://github.com/kdlucas/byte-unixbench/tree/master/UnixBench
# cd UnixBench
# make
# ```
# TODO: make it python script

vm=${vm:-amd}
disks=${disks:-nvme1n1}
dir=/mnt/application/unixbench/byte-unixbench/UnixBench

for size in medium
do
	for disk in $disks
	do
		inv vm.start --type $vm --size $size \
      		--virtio-blk /dev/$disk --no-warn \
		--action ssh-cmd \
		--ssh-cmd "mount /dev/vdb /mnt" \
		--ssh-cmd "bash -c 'cd $dir; perl Run'" \
		--ssh-cmd "mv $dir/results $dir/$vm-direct-$size-$disk" \
		--ssh-cmd "cp -r $dir/$vm-direct-$size-$disk /share/bench-result/unixbench/"
	done
done
