import re
import numpy as np


def parse_boottime(filename):
    f = open(filename, "r")
    text = f.read()
    f.close()

    qemu_re = "[0-9]+:\sQEMU"
    ovmf_re = "[0-9]+:\s[0-9]+ OVMF"
    linux_re = "[0-9]+:\s[0-9]+ Linux"
    runtime_re = "[0-9]+:\s[0-9]+ Runtime"

    # TODO: QEMU may appear on the last line, and it should then be ignored

    qemu_times = re.findall(qemu_re, text)
    qemu_times = [int(q.split(":")[0]) for q in qemu_times]
    qemu_delay = qemu_times[-1] - qemu_times[0]

    ovmf_times = re.findall(ovmf_re, text)
    ovmf_times = [int(q.split(":")[0]) for q in ovmf_times]
    ovmf_delay = ovmf_times[-1] - ovmf_times[0]

    linux_times = re.findall(linux_re, text)
    linux_times = [int(q.split(":")[0]) for q in linux_times]
    linux_delay = linux_times[-1] - linux_times[0]

    runtime_times = re.findall(runtime_re, text)
    runtime_times = [int(q.split(":")[0]) for q in runtime_times]
    runtime_delay = runtime_times[-1] - runtime_times[0]

    return qemu_delay, ovmf_delay, linux_delay, runtime_delay


if __name__ == "__main__":
    qemu_vm, ovmf_vm, linux_vm, runtime_vm = parse_boottime("VM_0.txt")
    qemu_cvm, ovmf_cvm, linux_cvm, runtime_cvm = parse_boottime("CVM_1.txt")

    n = 5
    vm_res = np.zeros((n, 4))
    cvm_res = np.zeros((n, 4))
    for i in range(n):
        vm_res[i] = parse_boottime("VM_" + str(i) + ".txt")
        cvm_res[i] = parse_boottime("CVM_" + str(i) + ".txt")

    vm_avg = np.mean(vm_res, axis=0)
    vm_std = np.std(vm_res, axis=0)
    cvm_avg = np.mean(cvm_res, axis=0)
    cvm_std = np.std(cvm_res, axis=0)

    print("VM stats:")
    print(f"QEMU: {vm_avg[0]/1000000} ms, std: {vm_std[0]/1000000} ms")
    print(f"OVMF: {vm_avg[1]/1000000} ms, std: {vm_std[1]/1000000} ms")
    print(f"Linux: {vm_avg[2]/1000000} ms, std: {vm_std[2]/1000000} ms")
    print(f"Runtime: {vm_avg[3]/1000000} ms, std: {vm_std[3]/1000000} ms")

    print("CVM stats:")
    print(f"QEMU: {cvm_avg[0]/1000000} ms, std: {cvm_std[0]/1000000} ms")
    print(f"OVMF: {cvm_avg[1]/1000000} ms, std: {cvm_std[1]/1000000} ms")
    print(f"Linux: {cvm_avg[2]/1000000} ms, std: {cvm_std[2]/1000000} ms")
    print(f"Runtime: {cvm_avg[3]/1000000} ms, std: {cvm_std[3]/1000000} ms")
