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
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/mpstat/$DATE}
DURATION=${DURATION:-20}
INTERVAL=${INTERVAL:-1}
RANGE ${RANGE:-"ALL"}

set -u

mkdir -p $OUTDIR
cd $OUTDIR

echo "Start collecting data $DURATION seconds"

mpstat -P $RANGE $INTERVAL $DURATION | tee mpstat.txt &

wait $(jobs -p)

echo "Result saved: ${OUTDIR}"
