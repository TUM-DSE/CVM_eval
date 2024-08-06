#!/bin/bash

set -x

# auto detect if possible
lscpu | grep -q AMD-V > /dev/null
if [ $? -eq 0 ]; then
    CVM=${CVM:-"snp"}
else
    CVM=${CVM:-"tdx"}
fi

RESULTDIR=${RESULTDIR:-"bench-results"}
OUT=${OUT:-"plot"}

set -e
set -u
set -o pipefail

#inv boottime.plot-boottime --cvm $CVM --outdir $OUT --result-dir $RESULTDIR
#inv boottime.plot-boottime --cvm $CVM --no-prealloc --outdir $OUT --result-dir $RESULTDIR
#inv boottime.plot-boottime2 --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/boottime
#inv boottime.plot-boottime2 --cvm $CVM --cpu --outdir $OUT --result-dir $RESULTDIR/boottime
inv boottime.plot-boottime2 --cvm $CVM --no-prealloc --outdir $OUT --result-dir $RESULTDIR/boottime
inv boottime.plot-boottime2 --cvm $CVM --no-prealloc --cpu --outdir $OUT --result-dir $RESULTDIR/boottime
#inv boottime.plot-boottime3 --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/boottime
#inv boottime.plot-boottime3 --cvm $CVM --cpu --outdir $OUT --result-dir $RESULTDIR/boottime

if [ "$CVM" = "snp" ]; then
    inv boottime.plot-boottime-snp --cvm $CVM --cpu --outdir $OUT --result-dir $RESULTDIR/boottime
    inv boottime.plot-boottime-snp --cvm $CVM --cpu --outdir $OUT --result-dir $RESULTDIR/boottime --version 6.9_gmem_2m
fi

inv vmexit.plot-vmexit --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/vmexit

inv phoronix.plot-phoronix-memory --cvm $CVM --size medium --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv phoronix.plot-phoronix-memory --cvm $CVM --size large --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size medium --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size medium --no-rel --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size large --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size large --no-rel --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size numa --outdir $OUT --result-dir $RESULTDIR/phoronix
#inv npb.plot-npb --cvm $CVM --size numa --no-rel --outdir $OUT --result-dir $RESULTDIR/phoronix
inv npb.plot-npb-omp --cvm $CVM --size medium --outdir $OUT --result-dir $RESULTDIR/npb-omp
inv npb.plot-npb-omp --cvm $CVM --size large --outdir $OUT --result-dir $RESULTDIR/npb-omp
inv npb.plot-npb-omp --cvm $CVM --size xlarge --outdir $OUT --result-dir $RESULTDIR/npb-omp
inv unixbench.plot-unixbench --cvm $CVM --size medium --outdir $OUT --result-dir $RESULTDIR/unixbench
inv unixbench.plot-unixbench --cvm $CVM --size medium --no-rel --outdir $OUT --result-dir $RESULTDIR/unixbench

inv app.plot-application --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/application
inv app.plot-application --cvm $CVM --poll --outdir $OUT --result-dir $RESULTDIR/application
inv app.plot-application --cvm $CVM --no-rel --outdir $OUT --result-dir $RESULTDIR/application
#inv app.plot-sqlite --cvm $CVM --device nvme1n1 --outdir $OUT --result-dir $RESULTDIR/application
inv storage.plot-fio --cvm $CVM --device nvme1n1 --outdir $OUT --result-dir $RESULTDIR/fio
inv storage.plot-fio --cvm $CVM --device nvme1n1 --outdir $OUT --result-dir $RESULTDIR/fio --all
#inv storage.plot-fio --cvm $CVM --device nvme1n1 --poll --outdir $OUT --result-dir $RESULTDIR/fio

inv network.plot-ping --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-ping --cvm $CVM --mq --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode udp --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode udp --mq --outdir $OUT --result-dir $RESULTDIR/network
#inv network.plot-iperf --cvm $CVM --mode tcp --outdir $OUT --result-dir $RESULTDIR/network
#inv network.plot-iperf --cvm $CVM --mode tcp --mq --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode tcp --pkt 128K --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode tcp --mq --pkt 128K --outdir $OUT --result-dir $RESULTDIR/network

inv network.plot-iperf --cvm $CVM --mode udp --plot-all --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode udp --mq --plot-all --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-iperf --cvm $CVM --mode tcp --pkt 128K --plot-all --outdir $OUT --result-dir $RESULTDIR/network
#inv network.plot-iperf --cvm $CVM --mode tcp --mq --pkt 128K --plot-all --outdir $OUT --result-dir $RESULTDIR/network

inv network.plot-nginx --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-nginx --cvm $CVM --mq --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-redis --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-redis --cvm $CVM --mq --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-memcached --cvm $CVM --outdir $OUT --result-dir $RESULTDIR/network
inv network.plot-memcached --cvm $CVM --mq --outdir $OUT --result-dir $RESULTDIR/network
