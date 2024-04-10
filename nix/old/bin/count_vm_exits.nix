{ pkgs, ... }:
pkgs.writeScriptBin "count-vm-exits"
  ''
    #!/usr/bin/env bash
    sudo bpftrace -e 'tracepoint:kvm:kvm_exit { @[kstack] += 1; }'
  ''
