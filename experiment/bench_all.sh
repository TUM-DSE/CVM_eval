#!/bin/bash

export VM=intel
export DISKS="nvme0n1 nvme1n1"

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SECONDS=0

bash $(SCRIPTDIR)/bench_boottime.sh;
bash $(SCRIPTDIR)/bench_app.sh;
bash $(SCRIPTDIR)/bench_storage.sh;
bash $(SCRIPTDIR)/bench_phoronix.sh;
bash $(SCRIPTDIR)/bench_network.sh;
bash $(SCRIPTDIR)/bench_swiotlb.sh;

secs=$SECONDS
hrs=$(( secs/3600 )); mins=$(( (secs-hrs*3600)/60 )); secs=$(( secs-hrs*3600-mins*60 ))
printf 'Time spent: %02d:%02d:%02d\n' $hrs $mins $secs
