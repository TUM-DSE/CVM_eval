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
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/vmstat/$DATE}

set -u

mkdir -p $OUTDIR
cd $OUTDIR

vmstat -s > vmstat.txt

echo "Resut saved: ${OUTDIR}"
