# Development

## General setup
- Install [nix](https://nixos.org/)
    - Note: you do not need to use NixOS on the host. You need the Nix package manager.
    - There are several ways to install nix, but [nix-installer](https://github.com/DeterminateSystems/nix-installer) would be handy.
- `nix develop` (or `direnv allow`)

## Quick start
### AMD SEV-SNP
```
nix develop

# build software
inv build.build-qemu-snp
inv build.build-ovmf-snp

# build guest image for direct boot
inv build.build-guest-fs
# build linux kernel for direct boot
just setup-linux

# Start (using resource config "vislor" for test. Edit ./tasks/vm.py to change)
inv vm.start --type snp --hostname vislor
```

### Intel TDX
```
nix develop

# build software
inv build.build-qemu-tdx
inv build.build-ovmf-tdx

# build guest image for direct boot
inv build.build-guest-fs
# build linux kernel for direct boot
just setup-linux-tdx

# Start (using resource config "ian" for test. Edit ./tasks/vm.py to change)
inv vm.start --type tdx --hostname ian
```

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
- Note: some just commands might be out dated

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

## VM size configuration
`VMRESOURCES` in the [./tasks/vm.py](../tasks/vm.py) defines VM sizes. For
example, `inv vm.start --size small` use the configuration of
`VMRESOURES[<hostname>]["small"]`. By default the machine's hostname is
automatically used. We can specify the hostname using `--hostname` option.
Please update the `VMRESOURCES` when using this script with a new machine.

## File sharing
The repository directory is mounted in `/share` in the guest using virtio-9p.
We can also mount the directory manually:

```
mkdir -p /share
mount -t 9p -o trans=virtio,version=9p2000.L share /share
```

## Storage (virtio-blk)
- `inv vm.start --virtio-blk <path>` command create a virtio-blk backed by the file `<path>`.
- See the fio section in the [benchmark.md](./benchmark.md) for the detail.

## Network (virtio-nic)
- `inv vm.start --virtio-nic` command create a virtio-nic backed by a host bridge.
- See [network.md](./network.md) for the detail.

## Inv option examples
- Force swiotlb: `--virtio-iommu --extra-cmdline swiotlb=524288,force`
- Use idle polling: `--extra-cmdline idle=poll --name-extra -poll`
- Use halt idle polling: `--extra-cmdline cpuidle_haltpoll.force=Y --name-extra -haltpoll`

## Run automated command
- By default, `inv vm.start` launch a VM
- `inv` command has `--action` arguments, which we can automate processing
- See [../tasks/vm.py](../tasks/vm.py), specifically, `do_action()` for the detail
- We can also use `ssh-cmd` to quickly run command in the VM
```
inv vm.start --type amd --ssh-cmd "echo hi" --ssh-cmd "ls /"
```

## QA
### VM fails to boot (`inv vm.start` fails)
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
- Try
   - `nix-shell --repair`
   - `nix-collect-garbage -d`
   - `nix-store --verify --check-contents --repair`

### Change ssh port
- Edit [tasks/config.py](../tasks/config.py)

## Additional info
- See [./docs](./)
    - [Attestation](./attestation.md)
    - [Benchmarks](./benchmark.md)
    - [Software version](./software_version.md)
    - [Build software manually](./how_to_build.md)
    - [Note on Linux](./linux.md)
    - [Note on AMD SEV-SNP](./amd-snp.md)
    - [Note on Intel TDX](./tdx.md)
