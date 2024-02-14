NVME=${NVME:-/dev/nvme1n1}
NUM_CPUS=${NUM_CPUS:-8}
FIO_BENCHMARK=${FIO_BENCHMARK:-all}
FIO_JOB_PATH=${FIO_JOB_PATH:-/mnt/blk-bm.fio}
NO_DMCRYPT=${NO_DMCRYPT:-0}
AIO=${AIO:-native io_uring}
TAG=${TAG:-}
NO_NATIVE=${NO_NATIVE:-0}

SSH_PORT=${SSH_PORT:-2224}

echo "Using NVME: $NVME"
echo "Using NUM_CPUS: $NUM_CPUS"

NVME_NAME=$(basename $NVME)

#######################
# native w/o dm-crypt


if [ "$NO_DMCRYPT" -eq 1 ]; then
  if [ "$NO_NATIVE" -eq 0 ]; then
    for aio in ${AIO};
    do
        inv run.benchmark-native-virtio-blk-qemu \
           --ignore-warning \
           --stop-qemu-before-benchmark \
           --await-results \
           --fio-benchmark=${FIO_BENCHMARK} \
           --num-cpus=${NUM_CPUS} \
           --aio=${aio} \
           --rebuild-ovmf \
           --ssd-path=${NVME} \
           --fio-job-path=${FIO_JOB_PATH} \
           --benchmark-tag=native-no-dmcrypt-aio-${aio}-${NUM_CPUS}-${NVME_NAME}$TAG \
           --ssh-forward-port=${SSH_PORT}
    done
  fi

  #######################
  # SEV w/o dm-crypt

  for aio in ${AIO};
  do
      inv run.benchmark-sev-virtio-blk-qemu \
         --ignore-warning \
         --stop-qemu-before-benchmark \
         --fio-benchmark=${FIO_BENCHMARK} \
         --await-results \
         --num-cpus=${NUM_CPUS} \
         --aio=${aio} \
         --rebuild-ovmf \
         --ssd-path=${NVME} \
         --fio-job-path=${FIO_JOB_PATH} \
         --benchmark-tag=sev-no-dmcrypt-aio-${aio}-${NUM_CPUS}-${NVME_NAME}$TAG \
         --ssh-forward-port=${SSH_PORT}
  done

else

  #######################
  # Setup dm-crypt
  inv utils.cryptsetup-crypt-only --ignore-warning --ssd-path=${NVME}

  if [ "$NO_NATIVE" -eq 0 ]; then

    #######################
    # native w/ dm-crypt

    for aio in ${AIO};
    do
        inv run.benchmark-native-virtio-blk-qemu \
           --ignore-warning \
           --stop-qemu-before-benchmark \
           --fio-benchmark=${FIO_BENCHMARK} \
           --await-results \
           --dm-benchmark  \
           --num-cpus=${NUM_CPUS} \
           --aio=${aio} \
           --rebuild-ovmf \
           --ssd-path=${NVME} \
           --fio-job-path=${FIO_JOB_PATH} \
           --benchmark-tag=native-aio-${aio}-${NUM_CPUS}-${NVME_NAME}$TAG \
           --ssh-forward-port=${SSH_PORT}
    done
  fi

  #######################
  # SEV w/ dm-crypt

  for aio in ${AIO};
  do
      inv run.benchmark-sev-virtio-blk-qemu \
         --ignore-warning \
         --stop-qemu-before-benchmark \
         --fio-benchmark=${FIO_BENCHMARK} \
         --await-results \
         --dm-benchmark  \
         --num-cpus=${NUM_CPUS} \
         --aio=${aio} \
         --rebuild-ovmf \
         --ssd-path=${NVME} \
         --fio-job-path=${FIO_JOB_PATH} \
         --benchmark-tag=sev-aio-${aio}-${NUM_CPUS}-${NVME_NAME}$TAG \
         --ssh-forward-port=${SSH_PORT}
  done

#######################
# Stop QEMU

fi
inv utils.stop-qemu --ssh-port=${SSH_PORT}
