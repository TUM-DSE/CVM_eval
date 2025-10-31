# VM-VMM communication (VMEXIT) measurement

[./bench/](./bench) is a kernel module that executes several instructions which
normally cause VMEXIT and measure the latency.

## How to run
- This measurement is not automated
- Start VM (with disk boot)
```
inv vm.start --type intel --no-direct
```
- Build kernel module (see below)
- Run kernel module
```
just ssh
cd /share/benchmarks/vmexit/
insmod bench.ko
mkdir -p /share/bench-result/vmexit
dmesg > /share/bench-result/vmexit/tdx.txt
```

## Example
```
$ # build kernel module (see below)
$ insmod bench.ko
$ dmesg
[...]
[   69.128079] bench: Benchmarking cpuid
[   75.595051] bench: cpuid (rax=0, rcx=0) :
[   75.595057] bench:   17443427490 cycles (avg: 1744)
[   75.595059] bench:   6460487268 ns (avg: 646)
[  114.143702] bench: cpuid (rax=1, rcx=0) :
[  114.143708] bench:   103978085562 cycles (avg: 10397)
[  114.143710] bench:   38510147397 ns (avg: 3851)
[  120.603647] bench: cpuid (rax=2, rcx=0) :
[  120.603653] bench:   17424554841 cycles (avg: 1742)
[  120.603655] bench:   6453497416 ns (avg: 645)
[  159.240362] bench: cpuid (rax=11, rcx=0) :
[  159.240369] bench:   104215563630 cycles (avg: 10421)
[  159.240370] bench:   38598101590 ns (avg: 3859)
[  165.970030] bench: cpuid (rax=21, rcx=0) :
[  165.970036] bench:   18152002935 cycles (avg: 1815)
[  165.970038] bench:   6722920699 ns (avg: 672)
[  172.700258] bench: cpuid (rax=22, rcx=0) :
[  172.700265] bench:   18153491850 cycles (avg: 1815)
[  172.700266] bench:   6723472285 ns (avg: 672)
```

## Build kernel modules with nix

[./hello](./hello) is an example kernel module.

- How to build with Nix (NOTE: we can build the kernel module on the host)
```
cd hello
nix-shell '<nixpkgs>' -A linuxPackages_6_8.kernel.dev
make -C $(nix-build -E '(import <nixpkgs> {}).linuxPackages_6_6.kernel.dev' --no-out-link)/lib/modules/*/build M=$(pwd) modules
insmod ./hello.ko
```

- Build a kernel module for the kernel defined in the flake
```
cd ./vmexit
make -C $(nix build --no-link --print-out-paths .#nixosConfigurations.tdx-guest.config.boot.kernelPackages.kernel.dev)/lib/modules/*/build M=$(pwd) modules
```
