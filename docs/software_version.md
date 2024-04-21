# Software information
Here is a list of information on software versions that we confirm work.

## AMD SEV-SNP
AMD uses https://github.com/AMDESE to host the software stack for SEV.
snp-(host)-latest branch contains the latest version of the software for
SEV-SNP. Note that sometimes AMD force-pushes to these repositories, removing
the previous commits. Therefore, we use forked versions to track changes.
A branch name "snp-latest-202311110" means that the branch is a snapshot of the
snp-latest branch of that date.

### 2023-11-17
- *Currently deployed*
- Host: https://github.com/mmisono/linux/tree/snp-host-latest-20231117
    - Linux 6.6-rc1
- Guest: Linux 6.6 (mainline (LTS))
- QEMU: https://github.com/mmisono/qemu/tree/snp-latest-20231110
- OVMF: https://github.com/mmisono/edk2/tree/snp-latest-20231110

