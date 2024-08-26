#!/bin/bash
#
# 0. Download NPB from https://www.nas.nasa.gov/software/npb.html, or if you have installed NPB by phoronix-test-suite:
# cd /var/lib/phoronix-test-suite/installed-tests/pts/npb-1.4.5/NPB3.4.1/NPB3.4-OMP/
# 1. edit config/make.def and add "-fopenmp" to FLAGS
# 2. edit config/suite.def (copy suite.def.template) and change S to C
# 3. make

set -x

REPEAT=${REPEAT:-5}
OUT=${OUT:-out}
SIZE=${SIZE:-C}

mkdir -p $OUT

for prog in ft mg sp lu bt is ep cg ua
do 
    for i in `seq $REPEAT`
    do
        OMP_DISPLAY_ENV=TRUE OMP_WAIT_POLICY=        OMP_NUM_THREADS=$(nproc) ./${prog}.${SIZE}.x > $OUT/${prog}.${SIZE}.${i}.log
        OMP_DISPLAY_ENV=TRUE OMP_WAIT_POLICY=ACTIVE  OMP_NUM_THREADS=$(nproc) ./${prog}.${SIZE}.x > $OUT/${prog}.${SIZE}.active.${i}.log
        OMP_DISPLAY_ENV=TRUE OMP_WAIT_POLICY=PASSIVE OMP_NUM_THREADS=$(nproc) ./${prog}.${SIZE}.x > $OUT/${prog}.${SIZE}.passive.${i}.log
    done
done