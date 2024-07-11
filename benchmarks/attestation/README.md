# Attestation measurements for AMD SEV-SNP and Intel TDX

## AMD SEV-SNP
Simply run:
```
sudo su && nix develop
inv vm.start --type snp --action run-attestation-sev
```

## Intel TDX
Our Intel TDX attestation measurements are perfomed using the `ubuntu` image, as it is used
from the [`canonical tdx`](https://github.com/canonical/tdx.git) repository.
For the verification, we use the [`go-tdx-guest`](https://github.com/google/go-tdx-guest.git) repository from Google.

As a prepare phase, we run the `prepare_tdx_ubuntu_image.sh` script that creates the image (if it does not exist),
installs the appropriate tools and utilities, and adds the [`ssh-key`](.../../../../nix/ssh_key.pub) to enable passwordless access for our automation.
To perform the measurements, simply run:
```
cd tdx
./prepare_tdx_ubuntu_image.sh
inv vm.start --type tdx-ubuntu --no-direct --action run-attestation-tdx
```

## Results
The results are pretty printed and placed in the `bench-result/attestation` file tree.