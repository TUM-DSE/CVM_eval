# Benchmark

## Boottime evaluation
See ../benchmarks/boottime/

## VM-VMM communicaiotn (VMEXIT measurement)
See ../benchmarks/vmexit/

## Phoronix test suite (memory, applicaiton benchmark)
### Example

```
# run phoronix-test-suite pts/memory
inv vm.start --type normal --action="run-phoronix" --phoronix-bench-name="memory"
```

### Options
- `--phoronix-bench-name`: name of benchmark (e.g., "memory", run "pts/memory")

### Result
The result is saved as `{PROJECT_ROOT}/bench-result/phoronix/{vmname}/{bench-name}/%Y-%m-%d-%H-%M-%S.xml`.


## FIO (storage)
### Example
```
inv vm.start --type snp --virtio-blk /dev/nvme1n1 --action="run-fio" --fio-job="libaio"
```

### Options
- `--virtio-blk <path>`: A file or a device used for the virtio-blk backend
- `--fio-job <name>`: fio job file name. Job files are in the `{PROJECT_ROOT}/config/fio/`
- `--virito-blk-aio <name>`: QEMU's aio engine (native/threads/io_uring) (default: native)
- `--no-virito-blk-iothread`: Don't use QEMU's iothread (default: use iothread)
- `--no-virito-blk-direct`: Use host page cache (default: direct (QEMU uses `O_DIRECT` to open the backend file/device)

### Result
The result is saved as `{PROJECT_ROOT}/bench-result/fio/{vmname}/{jobname}/%Y-%m-%d-%H-%M-%S.json`
