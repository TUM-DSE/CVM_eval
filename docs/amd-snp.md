# Miscellaneous Notes on AMD SEV-SNP

## #VC exception handling in Linux
- Based on Linux 6.8
- #VC can happen in both user and kernel space
- [user-space entry point](https://github.com/torvalds/linux/blob/v6.8/arch/x86/kernel/sev.c#L1976)
- [kernel-space entry point](https://github.com/torvalds/linux/blob/v6.8/arch/x86/kernel/sev.c#L1924)

### Detail
- Main handler is [`vc_handle_exitcode()`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/kernel/sev.c#L1751)
- cpuid
    - The kernel contains code for both SEV(-ES) and SNP
        - SNP VM can have cpuid page
    - SNP
        - The main part is [`vc_hdnale_cpuid_snp()`](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/sev-shared.c#L933)
        - The handler tries to get cpuid [from the cpuid page](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/sev-shared.c#L396)
        - Then only call [VMGEXIT for fixup if needed](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/sev-shared.c#L437)
- rdmsr / wrmsr
    - [VMGEIXT `SVM_EXIT_MSR`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/kernel/sev.c#L1196)
- pio
    - [VMGEXIT `SVM_EXIT_IOIO`](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/sev-shared.c#L825)
- hypercall (`vmmcall`)
    - [VMGEIXT `SVM_EXIT_VMMCALL`](https://github.com/torvalds/linux/blob/v6.8/arch/x86/kernel/sev.c#L1706)

## Enable AVX 512 in the guest

_NOTE:_ Starting with QEMU 9.1, QEMU supports "-cpu host" for SEV-SNP [(commit)](https://github.com/qemu/qemu/commit/188569c10d5dc6996bde90ce25645083e9661ecb).

QEMU 8.1.5 requires to use not `-cpu host` but `-cpu EPYC-v4` to boot SNP guests, but this CPU model misses several CPUIDs.
Especially, AMD512-related CPUIDs are not enabled, resulting the guest application won't use AVX512.
This affects the performance of HPC and AI/ML applications.
We can manually enable these CPUIDs so that the guest can use AVX512.

### Check available AVX instructions reported by CPUID

- EPYC 9334 (on the host)
```
% cat /proc/cpuinfo | grep flags | head -n1 | sed -e 's/ /\n/g' | sort | uniq | grep avx
avx
avx2
avx512_bf16
avx512_bitalg
avx512bw
avx512cd
avx512dq
avx512f
avx512ifma
avx512vbmi
avx512_vbmi2
avx512vl
avx512_vnni
avx512_vpopcntdq
```

- QEMU `-cpu EPYC-v4` model
```
# cat /proc/cpuinfo | grep flags | head -n1 | sed -e 's/ /\n/g' | sort | uniq | grep avx
avx
avx2
```

We can enable AVX512 in the guest by manually adding features in the command line.

```
-cpu EPYC-v4,host-phys-bits=true,+avx512f,+avx512dq,+avx512cd,+avx512bw,+avx512vl,+avx512ifma,+avx512vbmi,+avx512vbmi2,+avx512vnni,+avx512bitalg
# +avx512vpopcntdq is not supported in QEMU 8.15. Future versions support it.
```

Now we get
```
# cat /proc/cpuinfo | grep flags | head -n1 | sed -e 's/ /\n/g' | sort | uniq | grep avx
avx
avx2
avx512_bitalg
avx512bw
avx512cd
avx512dq
avx512f
avx512ifma
avx512vbmi
avx512_vbmi2
avx512vl
avx512_vnni
```

### Comment
- Are there any other missing important CPUIDs?
