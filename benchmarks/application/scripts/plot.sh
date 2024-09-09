#!/usr/bin/env bash

for metric in vmexits cpu cache_misses dTLB_misses branch_misses ipc L1_misses L2_misses; do
    inv app.plot-tensorflow-db --metric $metric
    for bench in ua cg ep is lu mg sp ft bt; do
        inv app.plot-npb --metric $metric --bench $bench
    done
done

inv app.plot-tensorflow-db

for bench in ua cg ep is lu mg sp ft bt; do
    inv app.plot-npb --bench $bench
done
