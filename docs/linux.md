# Miscellaneous Notes on Linux

## SWIOTLB (bounce buffer)
### Commandline parameters
- `swiotlb=<int>`: number of IOTLB slabs for swiotlb
- `swiotlb=force`,`swiotlb=<int>,force` : force swiotlb
- `swiotlb=noforce`: disable swiotlb

### Default swiotlb size
- The default swiotlb is 64MB
    - https://github.com/torvalds/linux/blob/v6.8/include/linux/swiotlb.h#L36
- However, SEV/TDX-aware guests automatically adjust the swiotlb size so that
  the kernel has enough swiotlb
    - The size is `min(6% of the total memory, 1GB)`
- See: https://github.com/torvalds/linux/blob/v6.8/arch/x86/mm/mem_encrypt.c#L100-L118
- Linux also supports dynamic allocation of swiotlb
    - https://lwn.net/Articles/940973/
    - https://patchwork.kernel.org/project/linux-mips/cover/cover.1690871004.git.petr.tesarik.ext@huawei.com/

### How it works
- `dma_map*()` functions evantually call [`swiotlb_map()`](https://github.com/torvalds/linux/blob/v6.8/kernel/dma/swiotlb.c#L1472) if swiotlb is enabled.
- Note that `dma_alloc*()` functions do not use swiotlb even if `swiotlb=force`
    - `dma_alloc*()` converts allocated memory into shared memory
        - https://github.com/torvalds/linux/blob/v6.8/kernel/dma/direct.c#L369
    - If [Restricted DMA](https://lwn.net/Articles/841916/) is enabled, then DMA memory is allocated from swiotlb buffer.

### Check status
- debugfs
```
# cat /sys/kernel/debug/swiotlb/io_tlb_nslabs
524288
// slab size is 2048 (https://github.com/torvalds/linux/blob/v6.8/include/linux/swiotlb.h#L32)
// Example values:
// 524288 * 2048 (iotlb slb size) = 1GB
//  32768 * 2048 (iotlb slb size) = 64MB
# cat /sys/kernel/debug/swiotlb/io_tlb_used
400
# cat /sys/kernel/debug/swiotlb/io_tlb_used_hiwater
1291
```
- Check kernel messages
```
# dmesg | grep -i 'tlb'
[    0.007602] software IO TLB: SWIOTLB bounce buffer size adjusted to 1024MB
[    0.230293] software IO TLB: area num 8.
[    0.348533] Last level iTLB entries: 4KB 512, 2MB 255, 4MB 127
[    0.348534] Last level dTLB entries: 4KB 512, 2MB 255, 4MB 127, 1GB 0
[    0.550384] HugeTLB: registered 2.00 MiB page size, pre-allocated 0 pages
[    0.550386] HugeTLB: 28 KiB vmemmap can be freed for a 2.00 MiB page
[    0.596784] iommu: DMA domain TLB invalidation policy: lazy mode
[    0.720884] PCI-DMA: Using software bounce buffering for IO (SWIOTLB)
[    0.720886] software IO TLB: mapped [mem 0x0000000032600000-0x0000000072600000] (1024MB)
[    0.768479] software IO TLB: Memory encryption is active and system is using DMA bounce buffers
```
- Note: swiotlb is allocated by default even for the normal guest regardless the use of swtiolb
    - We should check debugfs and bpftrace (kprobe/tracepoint) to see if the swiotlb is actually used
- If swiotlb size is too small, the kernel prints `swiotlb buffer is full`
- bpftrace
```
# bpftrace -e 't:swiotlb:swiotlb_bounced { @++; } i:s:1 { if(@){print(@); clear(@);} }'
Attaching 2 probes...
@: 54
@: 55
@: 21
[...]
```

### Note on bounce buffer with virtio devices
- On a normal VM, virtio devices *do not use bounce buffers even with `swiotlb=force`*
- This is because [`vring_use_dma_api`](https://github.com/torvalds/linux/blob/v6.8/drivers/virtio/virtio_ring.c#L279) is false as the virtio device does not have the `VIRTIO_F_ACCESS_PLATFORM` (also known as `VIRTIO_F_IOMMU_PLATFORM`) feature bit
    - This is for letting the guest perform direct memory access without any IOMMU involvement
- QEMU enabes `VIRTIO_F_ACCESS_PLATFORM` feature bit when the guest is a CVM
    - See https://github.com/qemu/qemu/commit/9f88a7a3df11a5aaa6212ea535d40d5f92561683
- To force `VIRTIO_F_ACCES_PLATFORM` feature, add `iommu_platform=on,disable-modern=off,disable-legacy=on` to the virtio option
    - Example: `-device virtio-net-pci,netdev=en0,iommu_platform=on,disable-modern=off,disable-legacy=on`
- We can check the virtio features as following
```
# cat /sys/devices/pci0000\:00/0000\:00\:03.0/virtio1/features
0010010000000001111101010000110010000000100000000000000000000000
                                 ^
                                 VIRTIO_F_ACCESS_PLATFORM(33)
```

## virtio-nic
### Multi queues
- QEMU
    - Create multiqueue tap: `sudo ip tuntap add tap0 mode tap multi_queue`
    - Option example:
    ```
        -netdev tap,id=en0,ifname=tap0,script=no,downscript=no,vhost=on,queues=8
        -device virtio-net-pci,netdev=en0,mq=on,vectors=18
    ```
- Kernel
    - RSS is enabled by default
    - Check
    ```
    # nix run nixpkgs#ethtool -- -l eth1
    Channel parameters for eth1:
    Pre-set maximums:
    RX:             n/a
    TX:             n/a
    Other:          n/a
    Combined:       4
    Current hardware settings:
    RX:             n/a
    TX:             n/a
    Other:          n/a
    Combined:       4

    # nix run nixpkgs#ethtool -- -x eth1
    RX flow hash indirection table for eth1 with 4 RX ring(s):
    Operation not supported
    RSS hash key:
    Operation not supported
    RSS hash function:
        toeplitz: on
        xor: off
        crc32: off

    # ls -1 /sys/devices/pci0000\:00/0000\:00\:05.0/msi_irqs/
    35
    36
    37
    38
    39
    40
    41
    42
    43

    # ls /sys/class/net/eth1/queues/
    rx-0  rx-1  rx-2  rx-3  tx-0  tx-1  tx-2  tx-3
    ```

## virtio-blk
### Multi queues
- QEMU
    - Use `-device -virtio-blk-pci,num_queues=4,...`
    - By deafult, `num-queues` is the number of vCPUs (it should be ideal)
    - See: https://github.com/qemu/qemu/commit/1436f32a84c3fda61d0d80302e24d641d3f3f839
- Kernel
    - Check number of queues
    ```
    # ls /sys/block/vdb/mq/
    0  1  2  3  4  5  6  7

    # cat /proc/interrupts
    [...]
     27:       1258          0          0          0          0          0          0          0  PCI-MSIX-0000:00:02.0   1-edge      virtio0-req.0
     28:          0        840          0          0          0          0          0          0  PCI-MSIX-0000:00:02.0   2-edge      virtio0-req.1
     29:          0          0       1474          0          0          0          0          0  PCI-MSIX-0000:00:02.0   3-edge      virtio0-req.2
     30:          0          0          0        378          0          0          0          0  PCI-MSIX-0000:00:02.0   4-edge      virtio0-req.3
     31:          0          0          0          0         83          0          0          0  PCI-MSIX-0000:00:02.0   5-edge      virtio0-req.4
     32:          0          0          0          0          0        241          0          0  PCI-MSIX-0000:00:02.0   6-edge      virtio0-req.5
     33:          0          0          0          0          0          0        135          0  PCI-MSIX-0000:00:02.0   7-edge      virtio0-req.6
     34:          0          0          0          0          0          0          0        107  PCI-MSIX-0000:00:02.0   8-edge      virtio0-req.7
    ```
### Queue polling
- Kernel
    - Use `virtio_blk.poll_queues=<N>` parameter to enable virtio-blk queue polling
    - See: https://github.com/torvalds/linux/commit/4e0400525691d0e676dbe002641f9a61261f1e1b

## NVMe
### Queue polling
- Use `nvme.poll_queues=<N>` parameter to enable NVMe queue polling
- Also enable `/sys/block/<disk>/io_poll`: https://docs.kernel.org/admin-guide/abi-stable.html#abi-sys-block-disk-queue-io-poll

