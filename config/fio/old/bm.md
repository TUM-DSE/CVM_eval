# BM - What to watch out for

## Applying Polling Techniques to QEMU KVM 17

```
Benchmark Configuration

Intel Xeon E5-2620 v2 @ 2.10GHz (Q3'13, 6 cores, 2 hyperthreads/core)
64 GB RAM
1 vCPU guest /w 4 GB RAM (no thread pinning, saw no improvement)
Intel DC P3700 SSD (NVMe 400 GB)

QEMU: qemu.git/master (2.10.1-ish) /w Fam Zheng’s NVMe VFIO patches
Host & guest OS: Fedora kernel 4.11.8-300.fc26.x86_64
Host & guest tuned profile: latency-performance (CPUfreq governor: performance, I/O scheduler: deadline)
Virtio-blk /w iothread,aio=native,cache=none,format=raw

fio 4k randread /w direct=1,jobs=1,ioengine=libaio
```

- fio versions
- guest Linux Kernel version
- host Linux kernel version
- HW: CPU, SSD
- DRAM

=> PerfStorage CHEOPS '23
    - cpu, mem, storage, sw

## fio

```ini
[global]
filename=/path/to/disk
direct=1 # non-buffered IO
# SPDK BM guidelines
thread=1
engine=libaio # linux native async-io engine
norandommap=1 # generate random offset for IO (independent of previous offsets)
randrepeat=0 # RNG for generating offset is seeded in random manner

time_based=1
# runtime=600 # from Intel SPDK BM guidelines
# ramp_time=60 # from Intel SPDK BM guidelines
runtime=120 # PerChar CHEOPS '23
ramp_time=20 # PerChar CHEOPS '23


# bs, rw, iodepth, numjobs from spool
[alat randread]
stonewall
blocksize=4k
rw=randread
iodepth=1
numjobs=1

[alat randwrite]
# alat for r,w,randr,randw
stonewall
blocksize=4k
rw=randwrite
iodepth=1
numjobs=1

[alat read]
stonewall
blocksize=4k
rw=read
iodepth=1
numjobs=1

[alat write]
stonewall
blocksize=4k
rw=write
iodepth=1
numjobs=1


[bw read]
stonewall
blocksize=128k
rw=write
iodepth=128
numjobs=1

[bw write]
stonewall
rw=write
blocksize=128k
iodepth=128
numjobs=1


[iops mixread]
stonewall
blocksize=4k
rw=randrw
mixread=70
iodepth=32
numjobs=4

[iops mixwrite]
stonewall
blocksize=4k
rw=randrw
mixread=30
iodepth=32
numjobs=4

[iops randread]
stonewall
blocksize=4k
rw=randread
iodepth=32
numjobs=4

[iops randwrite]
stonewall
blocksize=4k
rw=randwrite
iodepth=32
numjobs=4
```

## QEMU:

for cpu: SPDK:
```
-cpu host -smp 1
-m 2048 -object memory-backend-file,id=mem,size=2048M,mem-
path=/dev/hugepages,share=on,prealloc=yes,host-nodes=0,policy=bind
```

- from KVM libblk + polling to qemu
```
-blockdev host_device,filename=/dev/nvme0n1,aio=native,cache=none

# alt: w/ file sys
-blockdev file,filename=test.img,aio=native,cache=none,format=raw,node-name=drive0
-device virtio-blk-pci,drive=drive0
```

## NUMA locality
- see [spdk bm guide](https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf) and [this kvm presentation](https://static.sched.com/hosted_files/kvmforum2020/46/KVM-Forum-2020_NVMe_BaremetalDockerKVM.pdf)

- explicit core usage via `taskset -a -c`

## SSD Preconditioning
- e.g.: one repo somewhere
- [spdk bm guide](https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf)

## PCIe link speed + width
- [spdk bm guide](https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf)

## BIOS config
- [spdk bm guide](https://ci.spdk.io/download/events/2017-summit/08_-_Day_2_-_Kariuki_Verma_and_Sudarikov_-_SPDK_Performance_Testing_and_Tuning_rev5_0.pdf)

# Check if polling works

https://www.spinics.net/lists/fio/msg08594.html
Check with
vmstat 1 and look at the interrupt rate. If it's about your IOPS
rate, then you're doing IRQ based completions. If it's closer to 0,
you're doing polled.
