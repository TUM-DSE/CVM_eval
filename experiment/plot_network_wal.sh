#!/bin/bash

set -x

set -e
set -u
set -o pipefail

CVM=${CVM:-"snp"}
SIZE=medium

inv network.plot-iperf --cvm $CVM --size $SIZE --mode udp --plot-hpoll --pkt 1460

