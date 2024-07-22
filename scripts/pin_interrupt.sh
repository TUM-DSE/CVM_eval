#!/bin/bash
cpu=1
for x in `cat /proc/interrupts | grep nvme1q| awk '{ print $1 }' | cut -d':' -f 1`
do
echo $cpu > /proc/irq/$x/smp_affinity
cpu=$(($cpu+1))
done
