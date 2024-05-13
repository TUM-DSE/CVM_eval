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

