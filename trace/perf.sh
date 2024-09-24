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

perf kvm --$FLAG stat -e kvm:kvm_exit,instructions,branch-misses,dTLB-load-misses,L1-dcache-load-misses -a sleep $DURATION 2>&1 | tee $OUTDIR/perf-stat.txt

echo "Result saved: ${OUTDIR}"
