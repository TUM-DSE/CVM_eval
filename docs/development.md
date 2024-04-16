# Development

## General setup
- Install [nix](https://nixos.org/)
- `nix develop` (or `direnv allow`)

## AMD SEV-SNP
### Build software
```
inv build.build-qemu-snp
inv build.build-omvf-snp

# build guest image for disk boot
inv build.build-normal-guest-image
inv build.build-snp-guest-image

# build guest image for direct boot
inv build.build-guest-fs
# build linux kernel for direct boot
just setup-linux
```

### How to boot
- Disk boot
    - This uses ./build/image/normal-guest-image.qcow2 or ./build/images/snp-guest-image.qcow2. These image contains the guest kernel.
    - See `just start-vm-disk` for the detailed command line.
    - Pros: Easy to build with nix.
    - Cons: Slow to boot. Difficult to modify the guest kernel.
- Direct boot (recommended)
    - This uses ./build/image/guest-image.qcow2. This image only contains NixOS file systems. Direct boot uses vmlinux in the (project_root)/../linux for the kernel. (see justfile for the detail).
    - See `just start-vm-direct` for the detailed command line.
    - Pros: Fast to boot. Easy to modify the guest kernel.
    - Cons: For now the kernel for the direct boot is not managed by Nix.

### Launch VM
- [justfile](../justfile) defines qemu commands for quick tests.
```
just start-vm-disk    # boot vm using the disk image
just start-snp-direct # boot snp vm with direct boot
just ssh              # ssh to the vm
```

- [tasks/vm.py](../tasks/vm.py) provides commands to launch and execute command in a controlled manner.
    - The default command attaches to the launched VM.
    - VM automatically terminates when the commands finishes.
    - We can extend "action" to perform automated experiments.
- Examples
```
# start normal vm
inv vm.start --type normal --size small
# start snp vm (snp requires sudo)
sudo inv vm.start --type snp
# start snp vm, run phoronix benchmark
sudo inv vm.start --type snp --action run-phoronix
```

### File sharing
The repository directory is mounted in `/share` in the guest using vritio-9p.

