#!/usr/bin/env bash
set -ex

VM=normal
#VM=snp
SIZE=medium
PROCESS=8
DATE=`date +%Y-%m-%d-%H-%M-%S`
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
PROJECTPATH=$(dirname $(dirname $SCRIPTPATH))
DESTIP=172.44.0.2
DESTPORT=7175

DIR=${PROJECTPATH}/bench-result/network/iperf/${VM}-direct-${SIZE}/${DATE}
mkdir -p ${DIR}

for pkt in 64 128 256 512 1024 1460
do
    # -u :udp
    # -b 0 : no bandwidth limit
    # -i 1 : report interval 1s
    # -P 8 : 8 parallel streams
    iperf -c ${DESTIP} -p ${DESTPORT} -u -b 0 -i 1 -l ${pkt} -P ${PROCESS} > ${DIR}/iperf-udp-${pkt}.txt
done

for pkt in 64 128 256 512 1K 32K 128K
do
    # TCP
    # -i 1 : report interval 1s
    # -P 8 : 8 parallel streams
    iperf -c ${DESTIP} -p ${DESTPORT} -b 0 -i 1 -l ${pkt} -P ${PROCESS} > ${DIR}/iperf-tcp-${pkt}.txt
done

DIR=${PROJECTPATH}/bench-result/network/ping/${VM}-direct-${SIZE}/${DATE}
mkdir -p ${DIR}
# for pkt in 56 120 248 504 1016 1452
for pkt in 64 128 256 512 1024 1460
do
    ping -s ${pkt} ${DESTIP} -c30 -i0.1 > ${DIR}/ping-${pkt}.txt
done

