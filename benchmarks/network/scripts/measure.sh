#!/usr/bin/env bash
remote=false
if [ "$2" = "remote" ]; then
    remote=true
fi

repeat=$1

bash ./ping.sh $repeat $remote
bash ./iperf_tcp.sh $repeat $remote
bash ./iperf_udp.sh $repeat $remote
bash ./nginx.sh $repeat $remote
bash ./memtier.sh $repeat $remote
