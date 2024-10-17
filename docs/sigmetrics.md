## Benchmark information on the SIGMETRICS'25 paper

### Overview
- [experiment](../experiment) contains benchmark scripts
    - Run the script like `VM=snp ./experiment/bench_network.sh`
        - "VM" would be `amd`, `snp`, `intel` or `tdx`
    - The results are saved in `./bench-result`
- [experiment/plot_all.sh](../experiment/plot_all.sh) contains plot commands
    - If the plot command fails, then probably some results are missing
- *!!NOTE: some scripts are configured to use a physical disk (e.g., `/dev/nvme1n1`). Check the script running it and correct it if necessary*

### Software
- AMD SEV-SNP: https://github.com/TUM-DSE/CVM_eval/tree/checkpoint-sub-20240808-snp
    - Host: Linux 6.8
- Intel TDX: https://github.com/TUM-DSE/CVM_eval/tree/checkpoint-sub-20240808
    - Host: Linux 6.8 (canonical/tdx Ubuntu 24.04)

### Boottime
- [experiment/bench_boottime2.sh](../experiment/bench_boottime2.sh)
- Note: this script measures boottime with and without memory prealloc but some QEMU versions do not support prealloc option.

### Memory
- phoronix: [experiment/bench_phoronix.sh](../experiment/bench_phoronix.sh)
- mlc: Just run `inv vm.start --type snp --action run-mlc`
- mmap time: [experiment/run_mmap_time.sh](../experiment/run_mmap_time.sh)

### VMEXIT
- This evaluation is not automated. We manually install kernel module and get
  the result
- E.g.
```
# ssh to the machine
cd /share/benchmarks/vmexit/bench
insmod bench.ko
dmesg > /share/bench-result/vmexit/snp.txt
```
- See [benchmarks/vmexit](../benchmarks/vmexit) for the detail
- The plot script assumes that the results are saved as the `./bench-result/vmexit/{amd,snp,intel,tdx}.txt`

### Application (blender, pytorch, tensorflow)
- [experiment/bench_app.sh](../experiment/bench_app.sh)
- Note: this uses `/dev/nvme1n1` by default. The script first copy (rsync) the `benchmarks` directory to the disk and execute the benchmark there. Sometimes, copy fails for some reason. In that case, we can first try to copy the file by running a random benchmark (e.g., `inv vm.start --type amd --action="run-blender" --virtio-blk /dev/nvme1n1 --nowarn`), and then run benchmark script again.

### Unixbench
- [experiment/run_unixbench.sh](../experiment/run_unixbench.sh)
- Note: this uses `/dev/nvme1n1` by default

### NPB-OMP
- [experiment/npb_bench.sh](../experiment/npb_bench.sh)
- Set `OUT` for the result directory (e.g., `OUT=/share/bench-result/npb-omp/amd-direct-medium/`)

### Network, Storage
- [experiment/bench_network.sh](../experiment/bench_network.sh)
- [experiment/bench_storage.sh](../experiment/bench_storage.sh)
    - Note: this uses `/dev/nvme1n1` by default and erase the data!
- [experiment/bench_swiotlb.sh](../experiment/bench_swiotlb.sh)
    - Note: this uses `/dev/nvme1n1` by default and erase the data!
- idle poll, haltpoll experiments
    - Change `SWIOTLB_OPTION` in the `bench_swiotlb.sh` with
        - Use idle polling: `--extra-cmdline idle=poll --name-extra -poll`
        - Use halt idle polling: `--extra-cmdline cpuidle_haltpoll.force=Y --name-extra -haltpoll`

