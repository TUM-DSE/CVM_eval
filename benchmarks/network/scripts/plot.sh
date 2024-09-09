#!/usr/bin/env bash

for metric in vmexits cpu ipc cache_misses dTLB_misses iTLB_misses branch_misses ipc L1_misses L2_misses instructions; do
    inv network.plot-iperf-tcp --metric $metric
    inv network.plot-iperf-udp --metric $metric
    inv network.plot-memtier-db --metric $metric
    inv network.plot-nginx-db --metric $metric
done

inv network.plot-iperf-tcp
inv network.plot-iperf-udp
inv network.plot-memtier-db
inv network.plot-nginx-db
inv network.plot-ping-db
