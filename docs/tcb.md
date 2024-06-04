# TCB size evaluation
- Measure lines of code (LoC) and binary size of software components

## Linux kernel
- See: https://github.com/gramineproject/gramine-tdx/discussions/11
- In the first terminal
```
just clean-linux
just configure-linux
```
- In the secon dterminal
```
just build-linux-shell
cd ../linux
mv .git .git.hide
inotifywait -m -r -e open --format '%w%f' -o kernel_build.log $PWD
```
- In the first teminal again
```
just build-linux
```
- In the second terminal again
```
cat kernel_build.log | cut -c `pwd | wc -c | awk '{print $1 + 1}'`- | sort -u \
    | grep -E "\.c$|\.h$|\.H$|\.s$|\.S$" \
    | grep -v -E "^\.|^certs|^samples|^scripts|^tools|^usr" > kernel_build.log.prepared
cloc --list-file=kernel_build.log.prepared
```
- Linux 6.8 w/ defconfig, kvm_guest.config, SNP
```
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
C                             2929         376789         459576        1764779
C/C++ Header                  3689         112269         234503         537522
Assembly                        64           1411           4227           5454
-------------------------------------------------------------------------------
SUM:                          6682         490469         698306        2307755
-------------------------------------------------------------------------------
```
- vmlinux size (vmlinux.bin is stripped version of vmlinux)
```
$ ls -lh ./arch/x86/boot/vmlinux.bin
-rw-r--r-- 1 masa users 13M Jun  4 13:28 ./arch/x86/boot/vmlinux.bin
```

## OVMF
- TBD

## ASP firmware
```
git clone https://github.com/amd/AMD-ASPFW
cd AMD-ASPFW
cloc ./fw
```
- FW version 1.55.25 [hex 1.37.19] (Commit 3ca6650dd35d878b3fcbe5c7f58b145eed042bbf)
```
-------------------------------------------------------------------------------
Language                     files          blank        comment           code
-------------------------------------------------------------------------------
C                               54           5205           5248          23934
C/C++ Header                    58           1118           2061           4904
Assembly                         2             23             28             52
PHP                              1              4              0             47
-------------------------------------------------------------------------------
SUM:                           115           6350           7337          28937
-------------------------------------------------------------------------------
```
