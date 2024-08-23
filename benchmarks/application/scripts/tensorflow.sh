#!/usr/bin/env bash

action="run-tensorflow"

for size in medium large numa; do
    for type in amd snp; do
        inv vm.start --size $size --type ${type} --action=${action}
        inv vm.start --size $size --type ${type} --action=${action}
    done

    #snp with idle polling
    inv vm.start --type snp --size $size --action=${action} --extra-cmdline idle=poll --name-extra -poll
done
