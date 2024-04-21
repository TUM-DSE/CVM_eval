# Boot time analysis

[./boot_time_eval.bt](./boot_time_eval.bt) records the timestamp of boot
events (in nanoseconds) and reports them.

## Example
```
% sudo bpftrace boot_time_eval.bt
Attaching 13 probes...
1407581856554402: QEMU: main
1407581873142468: QEMU: kvm_arch_init
1407581873154159: QEMU: sev_kvm_init
1407581884166406: QEMU: sev_kvm_init done
1407581889028140: QEMU: kvm_arch_init done
1407581897972933: QEMU: memory_region_init_rom_device
1407581898264595: QEMU: memory_region_init_rom_device done
1407581950310930: QEMU: sev_snp_launch_finish
1407585132170098: QEMU: sev_snp_launch_finish done
1407585132699182: QEMU: kvm_cpu_exec
1407585256432520: 0 OVMF: PEI main start
1407585682513340: 0 OVMF: PEI main start
1407585682648221: 0 OVMF: PEI main start
1407585721699495: 1 OVMF: PEI main end
1407585727294964: 100 OVMF: DXE main end
1407586595045073: 101 OVMF: DXE main start
1407588630387104: 102 OVMF: EXITBOOTSERVICE
1407588643515896: 230 Linux: kernel_start
1407590115761967: 231 Linux: init_start
1407591028557652: 240 Linux: systemd init end
```

## Detail
The scripts records the events in the following ways:

- Host side (QEMU): Use uprobe to trace functions. No QEMU modification is needed.
- Guest side (OVMF/Linux): Modify guest software so that it executes `outb(0xf4, val)`. bpftrace monitor this outb events by tracing the `kvm_pio` tracepoint event.
    - (This is a similar way of [qboot benchmark](https://github.com/bonzini/qboot/blob/master/benchmark.h))

Especially, we modify the following part of the guest software:
- OVMF: We modify PXE main and DXE main.
- Linux kernel: We modify `start_kernel()`, `kernel_init()` in init/main.c to
  record time when the kernel starts and the init starts.
- Linux user: We add systemd service which is executed after all other
  services are dispatched to record the time when the user system is ready.

