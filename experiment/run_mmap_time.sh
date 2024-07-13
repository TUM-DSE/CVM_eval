vm=${vm:-amd}
size=${size:-medium}

for i in `seq 10`
do
	outdir="/share/bench-result/memory/mmap-time/$vm-direct-$size"
	inv vm.start --type $vm --size $size \
	--action ssh-cmd \
	--ssh-cmd "gcc -O2 /share/benchmarks/memory/mmap_time.c" \
	--ssh-cmd "mkdir -p $outdir" \
	--ssh-cmd "bash -c './a.out | tee -a $outdir/1st.txt'" \
	--ssh-cmd "bash -c './a.out | tee -a $outdir/2nd.txt'"
done
