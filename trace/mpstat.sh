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
#OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/mpstat/$DATE}
DURATION=${DURATION:-20}
INTERVAL=${INTERVAL:-1}

set -u

mkdir -p $OUTDIR
cd $OUTDIR

echo "Start collecting data $DURATION seconds"

#iostat  -d -k -x -y $INTERVAL $DURATION > iostat.txt &
#mpstat -I CPU $INTERVAL $DURATION > mpstat.txt &
mpstat $INTERVAL $DURATION | tee mpstat.txt &

wait $(jobs -p)

echo "Resut saved: ${OUTDIR}"
