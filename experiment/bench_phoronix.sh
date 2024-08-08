#!/bin/bash

set -x
set -e
set -u
set -o pipefail

VM=tdx
EXTRA=""
#VM=intel
#EXTRA="--name-extra -tme-bypass"

for size in medium
do
    for type_ in $VM
    do
        for action in phoronix 
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}" --phoronix-bench-name "memory" $EXTRA
        done
    done
done

for size in medium
do
    for type_ in $VM
    do
        for action in phoronix 
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}" --phoronix-bench-name "npb" $EXTRA
        done
    done
done
