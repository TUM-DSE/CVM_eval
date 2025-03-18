# How to build software

We use nix to manage software we use. See [flake.nix](../flake.nix) for the detail.

The below describes how to build software manually.
See [software_version.md](./software_version.md) for the software versions and
repository URLs.

## AMD SEV-SNP

### QEMU
```
nix develop nixpkgs#qemu
cd qemu/
mkdir build
cd build
../configure --target-list=x86_64-softmmu
make -j$(nproc)

ls ./qemu-system-x86_64
```

### OVMF
```
nix develop nixpkgs#edk2
nix-shell -p nasm acpica-tools # we also need this
cd ovmf/
git submodule update --init --recursive
make -C BaseTools
. edksetup.sh --reconfig
GCCVERS="GCC5"

# for debug
nice build -q --cmd-len=64436 -DDEBUG_ON_SERIAL_PORT=TRUE -n $(getconf _NPROCESSORS_ONLN) ${GCCVERS:+-t $GCCVERS} -a X64 -p OvmfPkg/OvmfPkgX64.dsc

# for release
nice build -q --cmd-len=64436 -DDEBUG_ON_SERIAL_PORT=TRUE -n $(getconf _NPROCESSORS_ONLN) ${GCCVERS:+-t $GCCVERS} -a X64 -p OvmfPkg/OvmfPkgX64.dsc -b RELEASE

ls ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF*
# ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF_CODE.fd
# ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF_VARS.fd
# ./Build/OvmfX64/DEBUG_GCC5/FV/OVMF.fd
```

### OVMF w/ measured direct boot support
```
nix develop nixpkgs#edk2
nix-shell -p nasm acpica-tools # we also need this
cd ovmf/
git submodule update --init --recursive
make -C BaseTools
. edksetup.sh --reconfig
GCCVERS="GCC5"
touch ./OvmfPkg/AmdSev/Grub/grub.efi
nice build -q --cmd-len=64436 -DDEBUG_ON_SERIAL_PORT=TRUE -n $(getconf _NPROCESSORS_ONLN) ${GCCVERS:+-t $GCCVERS} -a X64 -p OvmfPkg/AmdSev/AmdSevX64.dsc
```

### Guest Linux kernel
Enable the following options.
```
AMD_MEM_ENCRYPT y
VIRT_DRIVERS y
SEV_GUEST m
X86_CPUID m
```

### Host Linux kernel
Enable the following options.
```
EXPERT y
AMD_MEM_ENCRYPT y
CRYPTO_DEV_CCP y
CRYPTO_DEV_CCP_DD m
CRYPTO_DEV_SP_PSP y
KVM_AMD_SEV y
MEMORY_FAILURE y
```

-----------

## Intel TDX

### QEMU
```
git clone https://github.com/intel-staging/qemu-tdx/
cd qemu-tdx
git checkout -b tdx-qemu-next origin/tdx-qemu-next
mkdir build
cd build
../configure --target-list=x86_64-softmmu
make -j$(nproc)
```
