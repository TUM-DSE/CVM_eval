# Miscellaneous Notes on AMD SEV-SNP

## Enable AVX 512 in the guest

QEMU 8.1.5 requires to use not `-cpu host` but `-cpu EPYC-v4` to boot SNP guests, but this CPU model misses several CPUIDs.
Especitally, AMD512-related cpuids are not enabled, resulting the guest application won't use AVX512.
This affects the performance of HPC and AI/ML applications.
We can manually enable these cpuids so that the guest can use AVX 512.

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
- Is there any other missing important cpuids?
