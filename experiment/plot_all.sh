#!/bin/bash
set -x
set -e
set -u
set -o pipefail

CVM=${CVM:-tdx}

inv boottime.plot-boottime --cvm $CVM
if [ "$CVM" == "tdx" ]; then
    inv boottime.plot-boottime --cvm $CVM --no-prealloc
fi
inv vmexit.plot-vmexit --cvm $CVM

inv phoronix.plot-phoronix-memory --cvm $CVM --size medium
inv phoronix.plot-phoronix-memory --cvm $CVM --size large
inv npb.plot-npb --cvm $CVM --size medium
inv npb.plot-npb --cvm $CVM --size large
inv npb.plot-npb --cvm $CVM --size numa

inv app.plot-application --cvm $CVM
inv app.plot-application --cvm $CVM --outname "application_vnuma.pdf" --sizes small --sizes medium --sizes large --sizes numa --sizes vnuma --labels small --labels medium --labels large --labels xlarge --labels vnuma
inv app.plot-sqlite --cvm $CVM --device nvme0n1
inv app.plot-sqlite --cvm $CVM --device nvme1n1

inv storage.plot-fio --cvm $CVM --device nvme0n1
inv storage.plot-fio --cvm $CVM --device nvme1n1

inv network.plot-ping --cvm $CVM
inv network.plot-ping --cvm $CVM --mq
inv network.plot-iperf --cvm $CVM --mode udp
inv network.plot-iperf --cvm $CVM --mode tcp
inv network.plot-iperf --cvm $CVM --mode udp --mq
inv network.plot-iperf --cvm $CVM --mode tcp --mq

inv network.plot-nginx --cvm $CVM
inv network.plot-redis --cvm $CVM
inv network.plot-memcached --cvm $CVM
inv network.plot-nginx --cvm $CVM --mq
inv network.plot-redis --cvm $CVM --mq
inv network.plot-memcached --cvm $CVM --mq
