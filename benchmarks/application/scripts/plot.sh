#!/usr/bin/env bash

for metric in vmexits cpu cache_misses dTLB_misses iTLB_misses branch_misses ipc; do
    inv app.plot-tensorflow-db --metric $metric
done

inv app.plot-tensorflow-db