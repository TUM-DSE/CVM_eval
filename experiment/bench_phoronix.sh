#!/bin/bash

set -x
set -e
set -u
set -o pipefail

VM=${VM:-intel}

for size in medium
do
    for type_ in $VM
    do
        for action in phoronix 
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}" --phoronix-bench-name "memory"
        done
    done
done

exit

for size in numa large
do
    for type_ in $VM
    do
        for action in phoronix 
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}" --phoronix-bench-name "npb"
        done
    done
done
