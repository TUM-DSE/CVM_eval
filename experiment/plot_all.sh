#!/bin/bash

set -x

# auto detect if possible
lscpu | grep -q AMD-V > /dev/null
if [ $? -eq 0 ]; then
    CVM=${CVM:-"snp"}
else
    CVM=${CVM:-"tdx"}
fi

set -e
set -u
set -o pipefail

#inv boottime.plot-boottime --cvm $CVM
#inv boottime.plot-boottime --cvm $CVM --no-prealloc
inv boottime.plot-boottime2 --cvm $CVM
inv boottime.plot-boottime2 --cvm $CVM --cpu
inv boottime.plot-boottime2 --cvm $CVM --no-prealloc
inv boottime.plot-boottime2 --cvm $CVM --no-prealloc --cpu
inv boottime.plot-boottime3 --cvm $CVM
inv boottime.plot-boottime3 --cvm $CVM --cpu
inv vmexit.plot-vmexit --cvm $CVM

inv phoronix.plot-phoronix-memory --cvm $CVM --size medium
#inv phoronix.plot-phoronix-memory --cvm $CVM --size large
inv npb.plot-npb --cvm $CVM --size medium
inv npb.plot-npb --cvm $CVM --size medium --no-rel
#inv npb.plot-npb --cvm $CVM --size large
#inv npb.plot-npb --cvm $CVM --size large --no-rel
#inv npb.plot-npb --cvm $CVM --size numa
#inv npb.plot-npb --cvm $CVM --size numa --no-rel
inv unixbench.plot-unixbench --cvm $CVM --size medium
inv unixbench.plot-unixbench --cvm $CVM --size medium --no-rel

inv app.plot-application --cvm $CVM
inv app.plot-application --cvm $CVM --poll
inv app.plot-application --cvm $CVM --no-rel
inv app.plot-sqlite --cvm $CVM --device nvme1n1
inv storage.plot-fio --cvm $CVM --device nvme1n1
inv storage.plot-fio --cvm $CVM --device nvme1n1 --poll

#if [ "$CVM" == "tdx" ]; then
#    inv app.plot-application --cvm $CVM --outname "application_vnuma.pdf" --sizes small --sizes medium --sizes large --sizes numa --sizes vnuma --labels small --labels medium --labels large --labels xlarge --labels vnuma
#    inv app.plot-application --cvm $CVM --outname "application_vnuma.pdf" --sizes small --sizes medium --sizes large --sizes numa --sizes vnuma --labels small --labels medium --labels large --labels xlarge --labels vnuma --no-rel
#    inv app.plot-sqlite --cvm $CVM --device nvme0n1
#    inv storage.plot-fio --cvm $CVM --device nvme0n1
#fi

inv network.plot-ping --cvm $CVM
inv network.plot-ping --cvm $CVM --mq
inv network.plot-iperf --cvm $CVM --mode udp
inv network.plot-iperf --cvm $CVM --mode udp --mq
#inv network.plot-iperf --cvm $CVM --mode tcp
#inv network.plot-iperf --cvm $CVM --mode tcp --mq
inv network.plot-iperf --cvm $CVM --mode tcp --pkt 128K
inv network.plot-iperf --cvm $CVM --mode tcp --mq --pkt 128K

inv network.plot-iperf --cvm $CVM --mode udp --plot-all
inv network.plot-iperf --cvm $CVM --mode udp --mq --plot-all
inv network.plot-iperf --cvm $CVM --mode tcp --pkt 128K --plot-all
inv network.plot-iperf --cvm $CVM --mode tcp --mq --pkt 128K --plot-all

inv network.plot-nginx --cvm $CVM
inv network.plot-nginx --cvm $CVM --mq
inv network.plot-redis --cvm $CVM
inv network.plot-redis --cvm $CVM --mq
inv network.plot-memcached --cvm $CVM
inv network.plot-memcached --cvm $CVM --mq
