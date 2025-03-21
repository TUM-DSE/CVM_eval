# Benchmark

- For the detail of sigmetrics evaluation, see [sigmetrics.md](./sigmetrics.md)

## Boottime evaluation
See [../benchmarks/boottime/](../benchmarks/boottime/)

## VM-VMM communicaiotn (VMEXIT measurement)
See [../benchmarks/vmexit/](../benchmarks/vmexit/)

## Phoronix test suite (memory and other benchmarks)
### Example

```
# run phoronix-test-suite pts/memory
inv vm.start --type normal --action="run-phoronix" --phoronix-bench-name="memory"
```

### Options
- `--phoronix-bench-name`: name of benchmark (e.g., "memory", run "pts/memory")

### Result
The result is saved as `{PROJECT_ROOT}/bench-result/phoronix/{vmname}/{bench-name}/%Y-%m-%d-%H-%M-%S.xml`.

### Estimated time
- `pts/memory`: ~1hr
    - install time dependency: unzip
- `pts/sysbench` (only CPU and memory): ~10m
    - install time dependency: pkg-config, autotool, autoconf, libaio, libtool
- `pts/compression`: ~1hr (8cores)
    - install time dependency: cmake, p7zip
- `pts/npb`: ~1hr (32cores), ~3hr (8cores)
    - install time dependency: gfortran
    - runtime dependency: mpi, bc

### Information on benchmarks
- [OpenBenchmarking.org](https://openbenchmarking.org/) lists the information on the Phoronix Test Suite
- For exmple, [information on Memory Test Suite (pts/memory)](https://openbenchmarking.org/suite/pts/memory)
- Also, there is a page for each benchmark (e.g., [pts/mbw](https://openbenchmarking.org/test/pts/mbw))
- You can check how actually the benchmark is executed by consulting definition file (e.g., [pts/mbw](https://openbenchmarking.org/innhold/0a063ad51b563eec53a6c34d37806366ce52e7f6))
    - Especitlly, `test-definition.xml` defines runtime parameters.
- Also see: http://perf.mvermeulen.com/phoronix-overview/

### Trouble shooting
- Check logs: `/var/lib/phoronix-test-suite/test-results/{name}/test-logs/`
- Directly run tests: `/var/lib/phoronix-test-suite/installed-tests/`
- Check env: `phoronix-test-suite diagnostics`
- If `inv` command fails, maybe the benchmark suite is not properly installed.
  Try to `ssh` to the vm and install and run the benchmark manually.

## FIO (storage)
### Example
```
inv vm.start --type snp --virtio-blk /dev/nvme1n1 --action="run-fio" --fio-job="libaio"
```

### Options
- `--virtio-blk <path>`: A file or a device used for the virtio-blk backend
- `--fio-job <name>`: fio job file name. Job files are in the `{PROJECT_ROOT}/config/fio/`
- `--virtio-blk-aio <name>`: QEMU's aio engine (native/threads/io_uring) (default: native)
- `--no-virtio-blk-iothread`: Don't use QEMU's iothread (default: use iothread)
- `--no-virtio-blk-direct`: Use host page cache (default: direct (QEMU uses `O_DIRECT` to open the backend file/device)

### Result
The result is saved as `{PROJECT_ROOT}/bench-result/fio/{vmname}/{jobname}/%Y-%m-%d-%H-%M-%S.json`

### Estimated time
- ~1hr

### Add a new fio job
- Put it `{PROJECT_ROOT}/config/fio/`
