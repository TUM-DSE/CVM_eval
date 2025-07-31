#!/bin/bash

set -x

set -e
set -u
set -o pipefail

CVM=${CVM:-"snp"}
SIZE=medium

inv network.plot-iperf --cvm $CVM --size $SIZE --mode udp --plot-all --pkt 1460

