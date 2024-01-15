# Quicke guide how to run current benchmarks

```bash
# use autocompletion to make your life easier
source <(inv-completion) 
# after every `inv` command, use `-h` to view avaible options (often very helpful)

# build benchmark image (may already be built)
# native benchmark w/o extra copy always works; check swiotlb=force isn't set
# in /proc/cmdline nor in the nix/native-guest-image.nix

# build benchmark image *WITH* zero-copy
inv build.build-nixos-bechmark-image
# build *WITHOUT* zero-copy
inv build.build-nixos-bechmark-image --no-cvm-io

# you can check inside the guest after doing any IO through dm-crypt if zero-copy is set
# inside guest:
dmesg | grep CVM

# run native benchmark WITHOUT CVM WITH DM-CRYPT (remove corresponding flag to not use dm-crypt)
inv run.benchmark-native-virtio-blk-qemu \
    --await-results \
    --dm-benchmark \
    --rebuild-ovmf \
    \ # --fio-benchmark=STRING \ # if you only with to run e.g. bw or bw write, use this flag
    --stop-qemu-before-benchmark

# run cvm benchmark; using zero-copy or not depends on the previous build command
run.benchmark-sev-virtio-blk-qemu \
    --await-results \
    --dm-benchmark \ # again, remove this flag if you don't want to use dm-crpyt
    --rebuild-ovmf \
    \ # --fio-benchmark=STRING \ # if you only with to run e.g. bw or bw write, use this flag
    --stop-qemu-before-benchmark

# results are saved to ./inv-fio-logs
# you can tag your results via `--benchmark-tag=STRING`
```
