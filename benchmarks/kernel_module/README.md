### Build kernel modules with nix

```
cd hello
nix-shell '<nixpkgs>' -A linuxPackages_6_6.kernel.dev
make -C $(nix-build -E '(import <nixpkgs> {}).linuxPackages_6_6.kernel.dev' --no-out-link)/lib/modules/*/build M=$(pwd) modules
insmod ./hello.ko
```
