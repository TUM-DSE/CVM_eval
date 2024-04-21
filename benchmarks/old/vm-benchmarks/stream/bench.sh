#!/usr/bin/env bash

STREAM=./STREAM/stream_c.exe

# Run benchmarks on one NUMA node

OMP_PROC_BIND=true OMP_NUM_THREADS=1  taskset -c 0    ${STREAM} >  1.txt
OMP_PROC_BIND=true OMP_NUM_THREADS=4  taskset -c 0-3  ${STREAM} >  4.txt
OMP_PROC_BIND=true OMP_NUM_THREADS=8  taskset -c 0-7  ${STREAM} > 16.txt
OMP_PROC_BIND=true OMP_NUM_THREADS=16 taskset -c 0-15 ${STREAM} > 16.txt
OMP_PROC_BIND=true OMP_NUM_THREADS=32 taskset -c 0-31 ${STREAM} > 32.txt
#OMP_PROC_BIND=true OMP_NUM_THREADS=56 taskset -c 0-56 ./stream > 56.txt
