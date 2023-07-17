# CVM_eval

## Instructions to launch SEV machines

### Prepare the host toolchain
Compile the custom OVMF and QEMU provided by AMD:

```bash
./build.sh <dir>
```

### Misc

- [config](.config/) folder contains some configurations for ubuntu cloudimg.
- Download an ubuntu image: `wget https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-amd64.img`
- before launching guests you should run `./prepare.sh`

This readme assumes ovmf and qemu are in `./usr`, i.e. that you run `./build.sh ./usr`, if that is not the case adapt the following commands to reflect your edit.

### Launch a NOSEV guest. 

```bash
sudo LD_LIBRARY_PATH=$LD_LIBRARY_PATH ./nosev.sh ./usr/qemu/usr/bin/
```

### Launch an AMD SEV-SNP guest. 

```bash
sudo LD_LIBRARY_PATH=$LD_LIBRARY_PATH ./sev.sh ./usr/qemu/usr/bin/
```

## Inside the guest VM, verify that AMD SEV-SNP is enabled:
`sudo dmesg | grep snp -i ` should indicate `Memory Encryption Features active: AMD SEV SEV-ES SEV-SNP`

## Interact with the machines
- SEV machine: connect using ssh `ssh -p 2222 ubuntu@localhost`
- NOSEV machine: connect using ssh `ssh -p 2223 ubuntu@localhost`
