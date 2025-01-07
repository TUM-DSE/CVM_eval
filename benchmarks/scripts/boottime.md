## Setup

Compile `exec_outb.c` in a VM. Create `libmy_outb.so` from `outb.c`. Copy the `startup_script_runtime.sh` script onto the VM.

## Measurements

Run `sudo bpftrace boot_time_eval.bt` in a separate terminal to get the results and then start the VM.

Once the VM has booted, measure the runtime boot time by manually running `startup_script_runtime.sh`. Close the `bpftrace` terminal **BEFORE** closing the VM, to avoid the `QEMU exit` event from appearing in the trace.

Parse the measurements with `plot_boottime.py`.
