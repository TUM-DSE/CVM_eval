#!/bin/bash

# To run this experiments
# Prerequisites:
# - AMD SEV-SNP enabled hardware and kernel
# - This is tested with
#   - AMD EPYC 7713P 64-Core Processor
#   - Linux 6.8.0-rc5 (see ./docs/software_version.md for the details)
#   - (graham server in our cluster)
# 0. Clone repository
# ```
#    git clone https://github.com/TUM-DSE/CVM_eval.git
#    git checkout -b wal-network-bench origin/wal-network-bench
#
#    # The branch already contains the results. Rename it to avoid any conflicts.
#    mv bench-result bench-result-bakup
# ```
# 1. Build necessary software (see ./docs/development.md for the details)
# ```
#    nix develop
#    inv build.build-qemu-snp
#    inv build.build-ovmf-snp
#    inv build.build-guest-fs
#    just setup-linux
# ```
# 2. Configure the network
# ```
#    just setup_bridge`
#    just setup_tap`
# ```
# 3. Run the experiment
# ```
#    sudo su # need to be sudo to launch SNP VMs
#    nix develop
#    bash ./experiments/bench_network_wal.sh
# ```
# 4. Plot results
# ```
#    bash ./expleriments/plot_network_wal.sh
#    ls ./plot/iperf_udp_1460_throughput.pdf
# ```

set -x
set -e
set -u
set -o pipefail

SWIOTLB_OPTION=' --virtio-iommu --extra-cmdline "swiotlb=524288,force"'
POLL_OPTION=' --virtio-iommu --extra-cmdline "idle=poll" --name-extra -poll'
HALTPOLL_OPTION=' --virtio-iommu --extra-cmdline "cpuidle_haltpoll.force=Y" --name-extra -haltpoll'

VM=${VM:-amd}
CVM=${CVM:-snp}
SIZE=medium

STARTTIME=$(date +%Y%m%d-%H%M%S)

# "vm", "vhost", "snp", "snp-vhost"
for size in $SIZE
do
    for type_ in $VM $CVM
    do
        for action in iperf-udp
        do
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"
            inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost
        done
    done
done

# "swiotlb", "vhost-swiotlb"
for size in $SIZE
do
    for type_ in $VM
    do
        for action in iperf-udp
        do
            for option in "$SWIOTLB_OPTION"
            do
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost $option
            done
        done
    done
done

# "snp-hpoll", "snp-vhost-hpoll"
for size in $SIZE
do
    for type_ in $CVM
    do
        for action in iperf-udp
        do
            for option in "$POLL_OPTION" "$HALTPOLL_OPTION"
            do
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm" $option
                inv vm.start --type ${type_} --size ${size} --virtio-nic --action="run-${action}" --virtio-nic-tap="tap_cvm"  --virtio-nic-vhost $option
            done
        done
    done
done

ENDTIME=$(date +%Y%m%d-%H%M%S)
echo "Start time: $STARTTIME"
echo "End time: $ENDTIME"
