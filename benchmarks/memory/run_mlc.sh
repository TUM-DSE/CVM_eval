#!/bin/bash

modprobe msr

SCRIPTDIR=$(dirname $0)
NUM_HUGEPAGES=`cat /proc/sys/vm/nr_hugepages`

if [ $NUM_HUGEPAGES -lt 4000 ]; then
    echo "Set the number of hugepages to 4000"
    echo 4000 > /proc/sys/vm/nr_hugepages
fi

sync; echo 3> /proc/sys/vm/drop_caches

if [ $# -eq 1 ]; then
    OUTDIR=/share/bench-result/mlc
    if [ ! -d $OUTDIR ]; then
        OUTDIR=./
    fi
    mkdir -p $OUTDIR
    OUTFILE=${1}
    OUT=${OUT:-$OUTDIR/$OUTFILE}
    echo "Result saved as ${OUT}"
    NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#steam-run -- $SCRIPTDIR/mlc | tee -a $OUT
else
    NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#steam-run -- $SCRIPTDIR/mlc
fi
