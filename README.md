# CVM IO

**NOTE:**
We are moving `just` commands to `inv` commands.
If you find a `just` command to be missing, assume a corresponding `inv` command exists.
Execute `inv --list` to view avaiable `inv` commands.

When adding new commands, please add them in the python scripts- not the just file.

## Important Build Info

Please configure `direnv` for your shell, or use `nix develop` before running commands.

### Native (non-SEV) Kernel Developement Flow (non-nix)

```bash
# to only compile
just build-linux
# to compile and start VM
just qemu-debug
# to attach to running VM via ssh
just ssh-into-qemu-native
# to run certain storage IO configuration
just vm-build # see SEV developement
just start-native-vm-virtio-blk # other configs available
```

### SEV Kernel Developement Flow (uses precompiled Kernel)

```bash
# compile same as in native
just build-linux
# to build vm image and OVMF and compile kernel
just vm-build
# to only build VM image and compile kernel
just img-build
# to run SEV VM with current built VM image
just start-sev-vm
# different storage IO configuraitons exist in justfile; to view:
just --list
just start-native-vm-virtio-blk
# attach to running SEV VM via ssh
just ssh-into-qemu-sev
```


## Important Benchmarking Info

### HW / Vislor specific
#### SSD
- model: Samsung NVMe SSD PM173X
- size: 1.5TB
- PCI (vislor): 0000:64:00.00
- Format: Data Size: 4KB ; Metadata Size: 0

#### NUMA
- vislor: NVMe SSD PM173X: 64:00.0
- vislor: NUMA node0: CPU(s): 0-31,64-96
- --> CPUs 4-8 on same node das NVMe SSD

#### PCIe
##### Link Capability:

```bash
$ sudo lspci | grep Non-Volatile | head -n 1 | cut -f 1 -d ' ' | xargs -n 1 sudo lspci -vvv -s | grep LnkCap
		LnkCap:	Port #0, Speed 16GT/s, Width x8, ASPM not supported
		LnkCap2: Supported Link Speeds: 2.5-16GT/s, Crosslink- Retimer+ 2Retimers+ DRS-
```
- 16GT/s

##### Link Status:
also 16 GT/s by 8 x width

```bash
$ sudo lspci | grep Non-Volatile | head -n 1 | cut -f 1 -d ' ' | xargs -n 1 sudo lspci -vvv -s | grep LnkSta
		LnkSta:	Speed 16GT/s, Width x8
		LnkSta2: Current De-emphasis Level: -6dB, EqualizationComplete+ EqualizationPhase1+
```

#### BIOS
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
