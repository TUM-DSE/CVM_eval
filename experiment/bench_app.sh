#!/bin/bash

set -x
set -e
set -u
set -o pipefail

#VM=${VM:-tdx}
#VM=${VM:-intel}
REPEAT=${REPEAT:-10}
DISK=${DISK:-nvme1n1}
#VM=intel
#EXTRA="--name-extra -tmebypass"
VM=tdx
EXTRA=""

for size in xlarge large medium small
do
    for type_ in $VM
    do
        for action in blender pytorch tensorflow
        do
            inv vm.start --type ${type_} --size ${size} --action="run-${action}" \
		    --virtio-blk /dev/$DISK --no-warn \
		    --repeat $REPEAT $EXTRA
        done
    done
done

