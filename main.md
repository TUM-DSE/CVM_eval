---
abstract: |
  We report a preliminary performance evaluation of AMD SEV (Secure
  Environment Virtualization) on a Linux system.
author:
- |
  {rob,ric}Castellotti\
  TU Munich
- |
  Masanori Misono\
  TU Munich
bibliography:
- reference.bib
title: |
  **Evaluating Confidential Computing with Unikernels\
  (Guided Research Project)**
---

# Environment

We run our experiments on ryan, we using a patched version of QEMU from
AMD. Do we need additional info about the system? Specify what is
enabled (SEV-SNP and other stuff) Specify the CPU
[\[tab:experiment-environment\]](#tab:experiment-environment){reference-type="autoref"
reference="tab:experiment-environment"} shows the detailed environment.
We use QEMU/KVM as a hypervisor. We assign the guest the same amount of
CPUs (16) and 16G of memory.

::: table*
  -------------- ------------------------------------------------------------------------------
  Host CPU       AMD EPYC 7713P 64-Cores
  Host Memory    HMAA8GR7AJR4N-XN (Hynix) 3200MHz 64 GB $\times$ 8 (512GB)
  Host Config    Automatic numa balancing disabled; Side channel mitigation default (enabled)
  Host Kernel    6.1.0-rc4 #1-NixOS SMP PREEMPT_DYNAMIC (NixOS 22.11)
  QEMU           7.2.0 (patched)
  OVMF           Stable 202211 (patched) ????
  Guest vCPU     16
  Guest Memory   16GB
  Guest Kernel   5.19.0-41-generic #42-Ubuntu SMP PREEMPT_DYNAMIC (Ubuntu 22.10 )
  Guest Config   No vNUMA; Side channel mitigation default (enabled)
  -------------- ------------------------------------------------------------------------------
:::

# Micro Benchmarks

## CPUID latency

lorem ipsum

::: {#tab:cpuid}
  leaf   description          
  ------ -------------------- --
  0x0    vendor info          
  0x2    cache info           
  0x15   TSC info (trusted)   
  0x16   TSC info             

  : cpuid leaf information
:::

::: {#tab:cpuid_0x0}
                       50%    95%    99%     max
  ----------------- ------ ------ ------ -------
  bare                0.05   0.05   0.05    0.09
  bare:tme            0.04   0.05   0.05    0.09
  bare:tme:bypass     0.04   0.05   0.05    6.06
  vm:bare             0.61   0.62   0.62   27.94
  vm:notdx            0.62   0.62   0.64    7.83
  vm:notdx:bypass     0.62   0.62   0.63    4.11
  vm:tdx              1.45   1.46   1.47   31.95
  vm:tdx:bypass       1.49   1.62   1.63   29.64

  : cpuid latency leaf: 0x0 (time: us)
:::

## Memory overhead

We measure the memory overhead of TDX using the following benchmarks
using phoronix-test-suite [@phoronix]. Here, we report normalized
overhead compared to the baremetal ("bare").

RAMSpeed [@ramspeed]

:   This measures the memory latency with several operations.
    [\[fig:ramspeed\]](#fig:ramspeed){reference-type="autoref"
    reference="fig:ramspeed"} shows the results.

Tinymembench [@tinymembench]

:   This benchmark measures the memory latency of the system.
    [\[fig:membench\]](#fig:membench){reference-type="autoref"
    reference="fig:membench"} shows the results.

MBW [@mbw]

:   This measures the memory bandwidth of the system.
    [\[fig:membench\]](#fig:membench){reference-type="autoref"
    reference="fig:membench"} shows the results.

We observe the followings from the results.

-   For the RAMSpeed benchmarks, we observe 3.3% overhead for "bare:tme"
    and 6.38% for "vm:tdx" in geometric mean.

-   For the Tinymembench benchmarks, we observe 5.95% overhead for
    "bare:tme" and 4.42% for "vm:tdx" in geometric mean.

-   For the MBW benchmarks, we observe 9.37% overhead for "bare:tme" and
    10.52% for "vm:tdx" in geometric mean.

-   The overhead of the memory bandwidth (MBW) is larger than the
    overhead of the memory latency (RAMSpeed, Tinymembench).

# Application Benchmarks {#sec:app:benchmark}

We measure several application benchmarks using Phoronix Benchmark
Suite [@phoronix]. We especially run compilation and NPB (NAS Parallel
Benchmarks) benchmarks as CPU-intensive applications and lz4 and SQLite
benchmarks as memory-intensive applications. Here, we report normalized
overhead compared to the normal virtual machine ("bare:vm").

[**NOTE**: TDX VM ("vm:tdx") may have additional overhead due to the
vCPU over-commitment.]{style="color: red"}

Compilation benchmarks [@compilation]

:   This measures compilation times of several applications.
    [\[fig:compilation\]](#fig:compilation){reference-type="autoref"
    reference="fig:compilation"} shows the results.

NAS parallel benchmarks (NPB) [@npb]

:   This measures the times of several MPI parallel applications.
    [\[fig:npb\]](#fig:npb){reference-type="autoref"
    reference="fig:npb"} shows the results.

LZ4 [@lz4]

:   This measures the compression and decompression time with LZ4
    algorithm. [\[fig:lz4\]](#fig:lz4){reference-type="autoref"
    reference="fig:lz4"} shows the results.

SQLite [@sqlite_bench]

:   This measures the time to perform a pre-defined number of insertions
    to a SQLite database.
    [\[fig:membench\]](#fig:membench){reference-type="autoref"
    reference="fig:membench"} shows the results.

We observe the followings from the results.

-   As of compilation and NPB benchmarks, we observe around 10 to up to
    60% overhead in the TDX VM ("vm:tdx"). However, vPCU over-commitment
    might affect these results, so we expect the actual performance will
    be better.

-   As of LZ4 benchmaks, both "vm:notdx" and "vm:tdx" have similar
    performance. This is because LZ4 is a memory-intensive application,
    and the main overhead comes from memory encryption/decryption. NPB
    and these results also highlight the importance of TME bypass if we
    want to eliminate the memory encryption overhead in non-TDX VMs.

-   As of SQLite benchmarks, we observe larger performance overhead in
    "vm:tdx" when copy size is larger than 32. This might be due to the
    vCPU over-commitment, but further investigation is needed.

# Remarks

This report presents the basic performance experiments on Intel TDX with
QEMU/KVM. Further experiments will include but not be limited to the
following.

-   More detailed breakdown of the overhead in TDX VM, including #VE and
    TDX call handling.

-   Performance evaluation on other hypervisors such as Cloud
    Hypervisor.

-   Effect of vNUMA. vNUMA is known to have a significant impact on the
    performance of VM.

-   Memory management time in VMs.

-   Performance effect of having multiple TDX and Non-TDX VMs.

-   Boot time. TDX requires a special memory configuration, which
    affects the boot time.

-   I/O performance with and without TDX-IO.

-   Attestation time.

-   Migration time.

# Appendix {#appendix .unnumbered}

#### Section 3.2 "BIOS Configurations"

-   lorem

#### Check MSR values

We can check related MSR values with the following script.

``` {.c language="c"}
```
