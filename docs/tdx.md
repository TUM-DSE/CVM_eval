# Miscellaneous Notes on Intel TDX

## #VE exception handling in Linux
- Based on Linux 6.8
- The exception handler: https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L684
- The #VE can happen in both user and kernel space

### #VE in user-space
- The TDX kernel [only handles cpuid](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L643), otherwise returns an error (resulting SEGV)
    - This means that user space I/O is prohibited even using `ioperm()`, etc.
    - Note that TDCALL is a privileged instruction (VMGEXIT is not).
- cpuid
    - The handler issues tdcall (`TDG.VP.VMCALL<Instruction.CPUID>`) only for CPUIDs for hypervisor communication (i.e., leaf range 0x40000000 - 0x4FFFFFFF).
    - Otherwise [it returns zero](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L354-L356)
    - Note: TDX module handles main cpuid leafs and returns a result without #VE

### #VE in kernel-space
- cpuid
    - Same as the user-spce #VE handling
- rdmsr / wrmsr
    - The handler issues [`TDG.VP.VMCALL<Instruction.RDMSR>`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L297) or [`TDG.VP.VMCALL<Instruction.WRMSR>`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L318) tdcalls
- pio 
    - The handler [issues tdcall `TDG.VP.VMCALL<Instruction.IO>`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L557)
- hypercall
    - The handler [does not handle hyparcall (vmcall instruction)](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L661)
    - The kernel should use [`kvm_hypercall*()`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/include/asm/kvm_para.h#L38-L39) if needed, which issues `tdcall` instead of `vmcall` if the guest is TDX guest.
- mmio (via ept violation)
    - Only [ept violation on shared memory is handled](https://github.com/torvalds/linux/blob/v6.8/arch/x86/coco/tdx/tdx.c#L673)

## Get TDX module info
- On Linux 6.8 kernel
```
% ls /sys/firmware/tdx/tdx_module/
attributes  build_date  build_num  major_version  metadata  minor_version  status  vendor_id
% cat /sys/firmware/tdx/tdx_module/build_num
0x000002ba
```

## Enable TDX on Dell PowerEdge R760
- Docs: https://infohub.delltechnologies.com/en-us/p/enabling-intel-r-tdx-on-dell-poweredge/

### Prerequisite
- 5th gen Intel Xeon Scalable Processors (or later)
- Install identical DIMMs for memory slot 1 to 8 (at least) per CPU socket
    - This is requirement to use SGX

### BIOS configuration
- Memory Settings
    - Memory Operating Mode: Optimizer Mode
    - Node interleaving: Disabled
- Processor settings
    - CPU Physical Address Limit: Disabled
        - This option is required to enable "Multiple Keys" for memory encryption
- System Security
    - Intel TXT: ON
    - Memory Encryption: Multiple Keys
    - Global Memory Integrity: Disabled
    - TME Encryption Bypass: Enabled (or Disabled)
    - TME-MT/TDX Key Split: non-zero value
    - TDX Secure Arbitration Mode Loader: Enabled
    - SGX On
        - We first need to enable SGX to enable TDX options

