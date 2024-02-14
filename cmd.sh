set -ex

NVME=/dev/nvme1n1
EXTRA_TAG="cvm-io"

#### DMCYPT
# NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long/libaio.fio AIO=io_uring TAG=-libaio-long bash bench.sh
# base
NO_NATIVE=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long/iou.fio    AIO=io_uring TAG=-iou-long-${EXTRA_TAG:-}    bash bench.sh
# NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long/iou_s.fio  AIO=io_uring TAG=-iou_s-long  bash bench.sh
# NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long/iou_c.fio  AIO=io_uring TAG=-iou_c-long  bash bench.sh
# NO_NATIVE=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long/iou_sc.fio AIO=io_uring TAG=-iou_sc-long-${EXTRA_TAG:-} bash bench.sh

#### NO DMCYPT
# NO_DMCRYPT=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long-no-dmcrypt/libaio.fio AIO=io_uring TAG=-libaio-long-${EXTRA_TAG} bash bench.sh
# base
# NO_DMCRYPT=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long-no-dmcrypt/iou.fio    AIO=io_uring TAG=-iou-long-${EXTRA_TAG}    bash bench.sh
# NO_DMCRYPT=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long-no-dmcrypt/iou_s.fio  AIO=io_uring TAG=-iou_s-long-${EXTRA_TAG}  bash bench.sh
# NO_DMCRYPT=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long-no-dmcrypt/iou_c.fio  AIO=io_uring TAG=-iou_c-long-${EXTRA_TAG}  bash bench.sh
# base
# NO_DMCRYPT=1 NVME=$NVME NUM_CPUS=8 FIO_JOB_PATH=/mnt/long-no-dmcrypt/iou_sc.fio AIO=io_uring TAG=-iou_sc-long-${EXTRA_TAG} bash bench.sh
