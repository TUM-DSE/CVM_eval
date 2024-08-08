#!/bin/bash

set -x

VIRT=$(systemd-detect-virt)
if [ $? -eq 0 ]; then
    V="guest"
else
    V="host"
fi

DATE=$(date '+%Y-%m-%d-%H-%M-%S')
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/perf/$DATE}
DURATION=${DURATION:-10}

set -e
set -u

mkdir -p $OUTDIR
cd $OUTDIR

if [ $V = "host" ]; then
    perf record -a -g -- sleep $DURATION
    perf report -i ./perf.data --no-children > report.txt
else
    just -f /share/justfile perf-record $DURATION $OUTDIR/perf.data
    # FIXME: currently report in the guest fails for some reason
    #just -f /share/justfile perf-report $OUTDIR/perf.data $OUTDIR/report.txt
fi

echo "Resut saved: ${OUTDIR}"

