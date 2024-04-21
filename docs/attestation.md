# Attestation

## AMD SEV-SNP
### Calculate guest launch measurement (on the host)
- Use [sev-snp-measure](https://github.com/virtee/sev-snp-measure)
```
% git clone https://github.com/virtee/sev-snp-measure
% cd sev-snp-measure
% nix run nixpkgs#python3 -- ./sev-snp-measure.py --mode snp --vcpus=4 --vcpu-type=EPYC-v4 --ovmf=../../CVM_eval/build/ovmf-amd-sev-snp-fd/FV/OVMF.fd
4af0aa02fe41302d34e508c1f1fff64e6364510360d70095d9582b0de384c20f24cc27bad6c9d0cd5f798d8b13b8e975
```

### Get attestation report (on the guest)
- Load sev-guest kernel module (if missing)
```
% modprobe sev-guest
% ls /dev/sev-guest
```
- Use [snpguest](https://github.com/virtee/snpguest) to obtain an attestaion report
```
% git clone https://github.com/virtee/snpguest
% cd snpguest
% nix-shell -p cargo rustc
% cargo build
# request attestation using random data
% ./target/debugs/snpguest attestation-report.bin random-request-file.txt --random
# show attestation measurement
% ./target/debugs/snpguest display attestation-report.bin
# -> measurement should match with the value calculated with the sev-snp-measure
[...]

Measurement:
4a f0 aa 02 fe 41 30 2d 34 e5 08 c1 f1 ff f6 4e
63 64 51 03 60 d7 00 95 d9 58 2b 0d e3 84 c2 0f
24 cc 27 ba d6 c9 d0 cd 5f 79 8d 8b 13 b8 e9 75

[...]
```

