#!/bin/bash
set -x
set -e
set -u
set -o pipefail

VM=intel
CVM=tdx

inv boottime.plot-boottime --vm $VM --cvm $CVM
inv boottime.plot-boottime --vm $VM --cvm $CVM --no-prealloc
inv vmexit.plot-vmexit --vm $VM --cvm $CVM

inv phoronix.plot-phoronix-memory --vm $VM --cvm $CVM
inv npb.plot-npb --vm $VM --cvm $CVM

inv app.plot-application --vm $VM --cvm $CVM
inv app.plot-application --vm $VM --cvm $CVM --outname "application_vnuma.pdf" --sizes small --sizes medium --sizes large --sizes numa --sizes vnuma
inv app.plot-sqlite --vm $VM --cvm $CVM --device nvme0n1
inv app.plot-sqlite --vm $VM --cvm $CVM --device nvme1n1

inv storage.plot-fio --vm $VM --cvm $CVM --device nvme0n1
inv storage.plot-fio --vm $VM --cvm $CVM --device nvme1n1

inv network.plot-ping --vm $VM --cvm $CVM
inv network.plot-ping --vm $VM --cvm $CVM --mq
inv network.plot-iperf --vm $VM --cvm $CVM --mode udp
inv network.plot-iperf --vm $VM --cvm $CVM --mode tcp
inv network.plot-iperf --vm $VM --cvm $CVM --mode udp --mq
inv network.plot-iperf --vm $VM --cvm $CVM --mode tcp --mq

inv network.plot-nginx --vm $VM --cvm $CVM
inv network.plot-redis --vm $VM --cvm $CVM
inv network.plot-memcached --vm $VM --cvm $CVM
inv network.plot-nginx --vm $VM --cvm $CVM --mq
inv network.plot-redis --vm $VM --cvm $CVM --mq
inv network.plot-memcached --vm $VM --cvm $CVM --mq
