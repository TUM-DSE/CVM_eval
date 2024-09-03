#!/bin/bash

set -x

VIRT=$(systemd-detect-virt)
if [ $? -eq 0 ]; then
    V="guest"
else
    V="host"
fi

DATE=$(date '+%Y-%m-%d-%H-%M-%S')
SCRIPTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/perf/$DATE}
DURATION=${DURATION:-10}

set -e
set -u

mkdir -p $OUTDIR
cd $OUTDIR

if [ $V = "host" ]; then
    perf stat -e kvm:kvm_exit -a sleep $DURATION 2>&1 | tee $OUTDIR/perf-stat.txt
else
    perf stat -e instructions,cycles,branch-misses,cache-misses,dTLB-load-misses,iTLB-load-misses,L1-dcache-load-misses,l2_cache_req_stat.ic_dc_miss_in_l2 -a sleep $DURATION 2>&1 | tee $OUTDIR/perf-stat.txt
fi

echo "Result saved: ${OUTDIR}"
