#!/usr/bin/env bash

action="run-npb"

for prog in ft mg sp lu bt is ep cg ua; do

    for size in small medium large numa; do
        for type in amd snp; do
            inv vm.start --size $size --type ${type} --action=${action} --npb-prog=${prog}
        done

        #snp with idle polling
        inv vm.start --type snp --size $size --action=${action} --npb-prog=${prog} --extra-cmdline idle=poll --name-extra -poll
    done

done
