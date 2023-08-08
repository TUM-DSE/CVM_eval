#!/bin/bash

if [ $# -lt 2 ]; then
    echo "usage: ./fio.sh <machine> <disk>"
    exit 1
fi

T=$2-$1

echo running benchmarks for $T

fio \
    --name="bw_read" \
    --filename="/mnt/a" \
    --iodepth="128" \
    --rw="read" \
    --size="1G" \
    --bs="128K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="bw_read-$T.json"

fio --name="bw_write" \
    --filename="/mnt/a" \
    --iodepth="128" \
    --rw="write" \
    --size="1G" \
    --bs="128K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="bw_write-$T.json"

fio --name="iops_randread" \
    --filename="/mnt/a" \
    --iodepth="32" \
    --rw="randread" \
    --size="1G" \
    --bs="4K" \
    --numjobs="4" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="iops_randread-$T.json"

fio \
    --name="iops_randwrite" \
    --filename="/mnt/a" \
    --iodepth="32" \
    --rw="randwrite" \
    --size="1G" \
    --bs="4K" \
    --numjobs="4" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="iops_randwrite-$T.json"

fio --name="iops_mixread" \
    --rwmixread="70" \
    --filename="/mnt/a" \
    --iodepth="32" \
    --rw="randread" \
    --size="1G" \
    --bs="4K" \
    --numjobs="4" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="iops_mixread-$T.json"

fio \
    --name="iops_mixwrite" \
    --rwmixwrite="30" \
    --filename="/mnt/a" \
    --iodepth="32" \
    --rw="randwrite" \
    --size="1G" \
    --bs="4K" \
    --numjobs="4" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="iops_mixwrite-$T.json"

fio \
    --name="al-randread"  \
    --filename="/mnt/a" \
    --iodepth="1" \
    --rw="randread" \
    --size="1G" \
    --bs="4K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="al_randread-$T.json"

fio --name="al-randwrite"  \
    --filename="/mnt/a" \
    --iodepth="1" \
    --rw="randwrite" \
    --size="1G" \
    --bs="4K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="al_randwrite-$T.json"

fio \
    --name="al-read"\
    --filename="/mnt/a"\
    --iodepth="1"\
    --rw="read" \
    --size="1G" \
    --bs="4K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="al_read-$T.json"

fio \
    --name="al-write"  \
    --filename="/mnt/a" \
    --iodepth="1" \
    --rw="write" \
    --size="1G" \
    --bs="4K" \
    --numjobs="1" \
    --runtime="60" \
    --output-format="json"  \
    --direct=1 \
    --output="al_write-$T.json"
