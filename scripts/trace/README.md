
## Scripts
- `bpftrace ./intel_kvm_vmexit_count.bt`
    - Count VMEXIT on Intel machine


## One-liners

```
# count kvm_exit numbers
bpftrace -e 't:kvm:kvm_exit { @[args->exit_reason]++; } '

# list kvm related tracepoints
bpftrace -l 't:*kvm*'

# list traceable kvm functions
bpftrace -l 'f:*kvm*'

# show detaiiled function information
bpftrace -lv 'f:vmlinux:tdx_kvm_hypercall'
```

## Nix
```e
# enter shell with bpftrace
nix shell bpftrace

# one-liner
sudo nix run bpftrace -- -h

# run the latest version
sudo nix run github:nixos/nixpkgs/nixos-unstable#bpftrace

# when flake is not enabled
sudo nix --extra-experimental-features 'nix-command flakes' run github:nixos/nixpkgs/nixos-unstable#bpftrace
```

