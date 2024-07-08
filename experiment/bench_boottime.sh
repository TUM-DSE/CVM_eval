#!/bin/bash

set -x

#VM=${VM:-tdx}
VM=${VM:-intel}

for size in small medium large numa
do
    for type_ in $VM
    do
        inv vm.start --type ${type_} --size ${size} --action="boottime" --repeat 10
        inv vm.start --type ${type_} --size ${size} --action="boottime" --repeat 10 --no-boot-prealloc --name-extra -no-prealloc
    done
done

