#!/bin/bash
#

# Usage: bash ./all.sh fio 30 1

set -x

VIRT=$(systemd-detect-virt)
if [ $? -eq 0 ]; then
    V="guest"
else
    V="host"
fi

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DURATION=${2:-10}
INTERVAL=${3:-1}
D=$(date '+%Y-%m-%d-%H-%M-%S')
DATE=${4:-$D}
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$1/$DATE/$V}

export OUTDIR DURATION INTERVAL

bash ${SCRIPTDIR}/perf.sh &
bash ${SCRIPTDIR}/stat.sh &

sleep $((DURATION + 5))
