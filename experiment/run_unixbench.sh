
# prepartion
# ```
# mkfs.ext4 /dev/vdb
# mount /dev/vdb /mnt
# mkdir -p /mnt/application/unixbench
# cd /mnt/application/unixbench
# git clone https://github.com/kdlucas/byte-unixbench/
# cd UnixBench
# make
# ```
# TODO: make it python script

vm=${vm:-snp}
disks=${disks:-nvme1n1}
dir=/mnt/application/unixbench/byte-unixbench/UnixBench

for size in medium
do
	for disk in $disks
	do
		inv vm.start --type $vm --size $size \
		--virtio-blk /dev/$disk --no-warn \
		--action ssh-cmd \
		--ssh-cmd "bash -c 'if ! mount /dev/vdb /mnt; then mkfs.ext4 /dev/vdb && mount /dev/vdb /mnt; fi'" \
		--ssh-cmd "bash -c 'if ! cd $dir; then mkdir -p /mnt/application/unixbench && git clone https://github.com/kdlucas/byte-unixbench /mnt/application/unixbench/byte-unixbench; fi'" \
		--ssh-cmd "bash -c 'cd $dir; make; perl Run'" \
		--ssh-cmd "mv $dir/results $dir/$vm-direct-$size-$disk" \
		--ssh-cmd "cp -r $dir/$vm-direct-$size-$disk /share/bench-result/unixbench/"
	done
done
