# CVM_eval

## Instructions to launch SEV machines

### Prepare the host toolchain
Compile the custom OVMF and QEMU provided by AMD:

```bash
./build.sh
```

## Misc

- [config](.config/) folder contains some configurations for ubuntu cloudimg.
- Download an ubuntu image: `wget https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-amd64.img`

## Prepare a NOSEV guest

```bash
qemu-img convert kinetic-server-cloudimg-amd64.img nosev.img
qemu-img resize nosev.img +20G
mkdir OVMF_files
sudo cloud-localds cloud-config-nosev.iso config/cloud-config-nosev.yml
cp ./usr/local/share/qemu/OVMF_CODE.fd ./OVMF_files/OVMF_CODE_nosev.fd
cp ./usr/local/share/qemu/OVMF_VARS.fd ./OVMF_files/OVMF_VARS_nosev.fd
```
## Launch a NOSEV guest. 

```bash
sudo LD_LIBRARY_PATH=$LD_LIBRARY_PATH ./nosev.sh
```

## Prepare an AMD SEV-SNP guest.

```bash
qemu-img convert kinetic-server-cloudimg-amd64.img sev.img
qemu-img resize sev.img +20G
mkdir OVMF_files
sudo cloud-localds cloud-config-sev.iso ./config/cloud-config-sev.yml
cp ./usr/local/share/qemu/OVMF_CODE.fd ./OVMF_files/OVMF_CODE_sev.fd
cp ./usr/local/share/qemu/OVMF_VARS.fd ./OVMF_files/OVMF_VARS_sev.fd
```

## Launch an AMD SEV-SNP guest. 

```bash
sudo LD_LIBRARY_PATH=$LD_LIBRARY_PATH ./sev.sh
```

## Inside the guest VM, verify that AMD SEV-SNP is enabled:
`sudo dmesg | grep snp -i ` should indicate `Memory Encryption Features active: AMD SEV SEV-ES SEV-SNP`

## Interact with the machines
- SEV machine: connect using ssh `ssh -p 2222 ubuntu@localhost`
- NOSEV machine: connect using ssh `ssh -p 2223 ubuntu@localhost`
