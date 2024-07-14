#!/bin/bash

set -x

VM=${VM:-tdx}
#VM=${VM:-intel}

for mem in 8 16 32 64 128 256
do
    for type_ in $VM
    do
        inv vm.start --type ${type_} --size boot-mem${mem} --action="boottime" --repeat 10
        inv vm.start --type ${type_} --size boot-mem${mem} --action="boottime" --repeat 10 --no-boot-prealloc --name-extra -no-prealloc
    done
done

for cpu in 1 8 16 28 56
do
    for type_ in $VM
    do
        inv vm.start --type ${type_} --size boot-cpu${cpu} --action="boottime" --repeat 10
        inv vm.start --type ${type_} --size boot-cpu${cpu} --action="boottime" --repeat 10 --no-boot-prealloc --name-extra -no-prealloc
    done
done

