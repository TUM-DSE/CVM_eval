#!/usr/bin/env bash

SCRIPT_DIR=$(
    cd "$(dirname "$0")"
    pwd
)

repeat=$1

for i in $(seq 1 $repeat); do
    bash "$SCRIPT_DIR/npb.sh"
    bash "$SCRIPT_DIR/tensorflow.sh"
done