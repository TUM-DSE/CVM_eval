# Development

## General setup
- Install [nix](https://nixos.org/)
    - Note: you do not need to use NixOS on the host. You need the Nix package manager.
    - There are several ways to install nix, but [nix-installer](https://github.com/DeterminateSystems/nix-installer) would be handy.
- `nix develop` (or `direnv allow`)

## Build software
```
# build software
inv build.build-qemu-snp
inv build.build-ovmf-snp

# build guest image for disk boot
inv build.build-normal-guest-image
inv build.build-snp-guest-image

# build guest image for direct boot
inv build.build-guest-fs
# build linux kernel for direct boot
just setup-linux
```
- Also see [how_to_build.md](./how_to_build.md)

## How to boot
- Disk boot
    - This uses ./build/image/normal-guest-image.qcow2 or ./build/images/snp-guest-image.qcow2. These image contains the guest kernel.
    - See `just start-vm-disk` for the detailed command line.
    - Pros: Easy to build with nix. Easy to manage kernel modules.
    - Cons: Slow to boot. Difficult to modify the guest kernel.
- Direct boot (recommended)
    - This uses ./build/image/guest-image.qcow2. This image only contains NixOS file systems. Direct boot uses vmlinux in the (project_root)/../linux for the kernel. (see justfile for the detail).
    - See `just start-vm-direct` for the detailed command line.
    - Pros: Fast to boot. Easy to modify the guest kernel.
    - Cons: Using kernel modules requires additional care. For now the kernel for the direct boot is not managed by Nix.

## Launch VM
- [justfile](../justfile) defines qemu commands for quick tests.
```
just start-vm-disk      # boot vm using the disk image
just start-snp-direct   # boot snp vm with direct boot
chmod 600 ./nix/ssh_key # update permission of the ssh key
just ssh                # ssh to the vm
```

- [tasks/vm.py](../tasks/vm.py) provides commands to launch and execute command in a controlled manner.
    - The default command attaches to the launched VM.
    - VM automatically terminates when the commands finishes.
    - We can extend "action" to perform automated experiments.
- Examples
```
# start normal vm on AMD machine
inv vm.start --type amd --size small
# start snp vm (NOTE: snp requires root)
sudo su && nix develop
inv vm.start --type snp
# start snp vm, run phoronix benchmark
inv vm.start --type snp --action run-phoronix
```

## File sharing
The repository directory is mounted in `/share` in the guest using vritio-9p.

## Storage (virtio-blk)
- `inv vm.start --virtio-blk <path>` command create a virtio-blk backed by the file `<path>`.
- See the fio section in the [benchmark.md](./benchmark.md) for the detail.

## Netowrk (virito-nic)
- `inv vm.start --virtio-nic` command create a virtio-nic backed by a host bridge.
- See [network.md](./network.md) for the detail.

## QA
### VM failes to boot (`inv vm.start` fails)
- SNP requires root. Also some operations (e.g., using a disk for virtio-blk) require root.
- Try `sudo su && nix develop && inv vm.start --type snp [...]`
- Also, `inv` command does not show qemu error messages. Try manually run QEMU
  to see the error message.
    - `inv vm.start` prints QEMU command line. We can copy and use it
        - When running QEMU command manually, change QMP path accordingly (e.g., /tmp/qmp.sock)

### `sudo inv ...` fails
- While some inv commands needs root, sometimes `sudo inv ...` does not work due to missing python libraries
- You can first become root (`sudo su`) then `nix develop`. Then the shell has all dependencies.

### nix-shell env does not work for some reason
- Try `nix-shell --repair`

