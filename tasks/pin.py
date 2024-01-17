import time
import sys
import os

from subprocess import call
from qmp import QEMUMonitorProtocol

# Adopted from https://github.com/64kramsystem/qemu-pinning/wiki/Python-pinning-script

def cpu_pin(qmp_sock, cpu_base=4):
    if not os.path.exists(qmp_sock):
        print(f'[PIN] {qmp_sock} does not exist')
        return

    qmp = QEMUMonitorProtocol(qmp_sock)

    count = 0
    while True:
        try:
            count += 1
            print("[PIN] Connecting to {}".format(sys.argv[1]))
            qmp.connect()
            break
        except Exception as e:
            print('[PIN] Failed to connect to QEMU: {}'.format(e))
            time.sleep(0.1)
            if count >= 100:
                exit(1)

    print('[PIN] Pin vCPUs')
    num_cpus = len(qmp.command('query-cpus-fast'))
    for cpu in qmp.command('query-cpus-fast'):
        tid = cpu['thread-id']
        cpuidx = cpu['cpu-index']
        try:
            cmd = ['taskset', '-pc', str(cpuidx+cpu_base), str(tid)]
            call(cmd)
        except OSError as e:
            print('[PIN] Failed to pin vCPU{}: {}'.format(cpuidx, e))
            exit(1)

    num_iothreads = len(qmp.command('query-iothreads'))
    if num_iothreads == 0:
        print('[PIN] No iothreads found')
        return
    print('[PIN] Pin iothreads')
    for i, cpu in enumerate(qmp.command('query-iothreads')):
        tid = cpu['thread-id']
        try:
            cmd = ['taskset', '-pc', str(cpu_base + num_cpus + i), str(tid)]
            call(cmd)
        except OSError as e:
            print('[PIN] Failed to pin vCPU{}: {}'.format(cpuidx, e))
            exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('[PIN] Usage: {} <qemu-socket>'.format(sys.argv[0]))
        sys.exit(1)
    sock = sys.argv[1]
    cpu_base = 4
    if len(sys.argv) == 3:
        cpu_base = int(sys.argv[2])
    cpu_pin(sock, cpu_base)

