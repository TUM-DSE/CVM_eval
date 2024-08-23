#!/usr/bin/env bash

SCRIPT_DIR=$(
    cd "$(dirname "$0")"
    pwd
)

remote=false
if [ "$2" = "remote" ]; then
    remote=true
fi

repeat=$1

for i in $(seq 1 $repeat); do
    bash "$SCRIPT_DIR/nginx.sh" $remote
    bash "$SCRIPT_DIR/memtier.sh" $remote
    bash "$SCRIPT_DIR/ping.sh" $remote
    bash "$SCRIPT_DIR/iperf_tcp.sh" $remote
    bash "$SCRIPT_DIR/iperf_udp.sh" $remote
done
