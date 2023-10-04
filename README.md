# Important Benchmarking Info

## HW / Vislor specific
### SSD
- model: Samsung NVMe SSD PM173X
- size: 1.5TB
- PCI (vislor): 0000:64:00.00
- Format: Data Size: 4KB ; Metadata Size: 0

### NUMA
- vislor: NVMe SSD PM173X: 64:00.0
- vislor: NUMA node0: CPU(s): 0-31,64-96
- --> CPUs 4-8 on same node das NVMe SSD

### PCIe
#### Link Capability:

```bash
$ sudo lspci | grep Non-Volatile | head -n 1 | cut -f 1 -d ' ' | xargs -n 1 sudo lspci -vvv -s | grep LnkCap
		LnkCap:	Port #0, Speed 16GT/s, Width x8, ASPM not supported
		LnkCap2: Supported Link Speeds: 2.5-16GT/s, Crosslink- Retimer+ 2Retimers+ DRS-
```
- 16GT/s

#### Link Status:
also 16 GT/s by 8 x width

```bash
$ sudo lspci | grep Non-Volatile | head -n 1 | cut -f 1 -d ' ' | xargs -n 1 sudo lspci -vvv -s | grep LnkSta
		LnkSta:	Speed 16GT/s, Width x8
		LnkSta2: Current De-emphasis Level: -6dB, EqualizationComplete+ EqualizationPhase1+
```

### BIOS
- version: 1.5.8
- mem freq: max perf
- cpu power mngmt: max perf -> disable P States ; enables power max performance
- turbo: disabled -> disable Turbo Mode
- c-states: disabled -> disable C States
- power profile: max io perf mode
- DF CState: disabled
- DF PState: disabled
- Logical Processer -> disable Hyperthreading
- determinism slider: performance ( determinism to control performance )
- node interleaving: didn't find option, but should be disabled ( as system shows NUMA nodes )

SEV:
- enabled SME
- enabled SNP
- enabled SNP memory coverage ( selects SNP )
