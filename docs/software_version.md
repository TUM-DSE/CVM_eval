# Software information
Here is a list of information on software versions that we confirm work.

## AMD SEV-SNP
AMD uses https://github.com/AMDESE to host the software stack for SEV.
snp-(host)-latest branch contains the latest version of the software for
SEV-SNP. Note that sometimes AMD force-pushes to these repositories, removing
the previous commits. Therefore, we use forked versions to track changes.
A branch name "snp-latest-202311110" means that the branch is a snapshot of the
snp-latest branch of that date.

### Sotware version table

| host kernel version | linux | ovmf | qemu |
| ------------------- | ----- | -----| -----|
| 6.10.0-rc7          | [kvm-next-20240717](https://github.com/mmisono/linux/tree/kvm-next-20240717) | [snp-latest-20240510](https://github.com/mmisono/edk2/tree/snp-latest-20240510) | [snp-latest-20240515](https://github.com/mmisono/qemu/tree/snp-latest-20240515) |
| 6.9.0-rc7           | [snp-host-latest-20240514](https://github.com/mmisono/linux/tree/snp-host-latest-20240514) | [snp-latest-20240510](https://github.com/mmisono/edk2/tree/snp-latest-20240510) | [snp-latest-20240515](https://github.com/mmisono/qemu/tree/snp-latest-20240515) |
| 6.8.0-rc5           | [snp-host-latest-20240221](https://github.com/mmisono/linux/tree/snp-host-latest-20240221) | [snp-latest-20231110](https://github.com/mmisono/edk2/tree/snp-latest-20231110) | [snp-latest-20240221](https://github.com/mmisono/qemu/tree/snp-latest-20240221) |
| 6.6.0-rc1           | [snp-host-latest-20231117](https://github.com/mmisono/linux/tree/snp-host-latest-20231117) | [snp-latest-20231110](https://github.com/mmisono/edk2/tree/snp-latest-20231110) | [snp-latest-20240221](https://github.com/mmisono/qemu/tree/snp-latest-20231110) |

Note: The latest kernel versions (6.9 >=) has a memory performance issue by default due to disabling 2MB THP: https://github.com/AMDESE/AMDSEV/issues/225

## Intel TDX
- Intel summarizes TDX software information [here](https://github.com/intel/tdx/wiki/TDX-KVM).
- Also, Canonical summarizes information on TDX on Ubuntu [here](https://github.com/canonical/tdx).
    - Using Ubuntu would make life easier for the most cases

### Sotware version table
| host kernel version | linux | ovmf | qemu |
| ------------------- | ----- | -----| -----|
| 6.8.0-rc1           | [kvm-upstream-next-20240122](https://github.com/mmisono/linux/tree/tdx-kvm-upstream-next-20240122) | [TDVF-20240105](https://github.com/mmisono/edk2/tree/TDVF-20240105) | [tdx-qemu-next-20231208](https://github.com/mmisono/qemu/tree/tdx-qemu-next-20231208) |

### Ubuntu 23.10
- Software stack: https://github.com/canonical/tdx/tree/mantic-23.10
- Host: Linux 6.5.0-10003-intel-opt
- Guest: Linux 6.7 (mainline)
- OVMF: 2023.05-2+tdx1.0
    - Also work: [edk2-stating/TDVF (c229fca)](https://github.com/tianocore/edk2-staging/commit/c229fca09ebc3ed300845e5346d59e196461c498)
- QEMU: 8.0.4 (Debian 1:8.0.4+dfsg-1ubuntu3+tdx1.0)
    - Repo: https://code.launchpad.net/~kobuk-team/ubuntu/+source/qemu/+git/qemu/+ref/tdx
    - I also tried several version of [intel-staging/qemu-tdx](https://github.com/intel-staging/qemu-tdx/) but none of them works with the kernel

#### How to build kobuk-team's QEMU
- Create a recipe file (See the bottom of https://code.launchpad.net/~kobuk-team/+recipe/tdx-qemu-mantic)
```
% cat qemu.recipe
# git-build-recipe format 0.4 deb-version {debversion}+tdx.{time}
lp:ubuntu/+source/qemu ubuntu/mantic
merge backport lp:~kobuk-team/ubuntu/+source/qemu tdx
```
- Clone repository using `git-build-recipe`
```
% sudo apt install git-build-recipe
% git-build-recipe --allow-fallback-to-native --no-build qemu.recipe build
```
- Build
```
% nix develop nixpkgs#qemu
% cd ./build/qemu
% mkdir ./build
% cd build
% ../configure --target-list=x86_64-softmmu --enable-kvm --firmwarepath=/usr/share/qemu:/usr/share/seabios:/usr/lib/ipxe/qemu --disable-install-blobs
% make -j$(nproc)

# XXX: for some reason, `--firmwarepath` does not work
# So copy necessary rom files in the directory where you run qemu-system-x86_64
% cp /usr/share/qemu/kvmvapic.bin .
% cp /usr/share/qemu/linuxboot_dma.bin .
% cp /usr/lib/ipxe/qemu/efi-virtio.rom .
```
