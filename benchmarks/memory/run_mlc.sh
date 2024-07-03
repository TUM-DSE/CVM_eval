#!/bin/bash

OUTDIR=/share/bench-result/mlc

if [ ! -d $OUTDIR ]; then
    OUTDIR=./
fi

mkdir -p $OUTDIR
OUTFILE=${1:-mlc.txt}
OUT=${OUT:-$OUTDIR/$OUTFILE}

modprobe msr

NUM_HUGEPAGES=`cat /proc/sys/vm/nr_hugepages`

if [ $NUM_HUGEPAGES -lt 4000 ]; then
    echo "Set the number of hugepages to 4000"
    echo 4000 > /proc/sys/vm/nr_hugepages
fi

sync; echo 3> /proc/sys/vm/drop_caches

echo "Result saved as ${OUT}"

#./mlc | tee -a mlc.log
NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#steam-run -- ./mlc | tee -a $OUT
