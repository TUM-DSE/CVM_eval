#!/bin/bash

set -x
set -e
set -u
set -o pipefail

VM=${VM:-intel}

for size in numa large medium small
do
    for type_ in $VM
    do
        for action in blender pytorch tensorflow
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}"
        done
    done
done

