#!/usr/bin/env bash

for metric in vmexits cpu cache_misses dTLB_misses iTLB_misses branch_misses ipc L1_misses L2_misses; do
    inv app.plot-tensorflow-db --metric $metric
    inv app.plot-tensorflow-db --metric $metric --norm insts
    for bench in ua ; do #cg ep is lu mg sp ft bt
        inv app.plot-npb --metric $metric --bench $bench
        inv app.plot-npb --metric $metric --bench $bench --norm insts
    done
done

inv app.plot-tensorflow-db

for bench in ua ; do # cg ep is lu mg sp ft bt
    inv app.plot-npb --bench $bench
done
