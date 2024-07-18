#!/bin/bash

set -x

VIRT=$(systemd-detect-virt)
if [ $? -eq 0 ]; then
    V="guest"
    DISK=${DISK:-vdb}
    NIC=${NIC:-eth1}
else
    V="host"
    DISK=${DISK:-nvme1n1}
    NIC=${NIC:-virbr_cvm}
fi

DATE=$(date '+%Y-%m-%d-%H-%M-%S')
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
OUTDIR=${OUTDIR:-$SCRIPTDIR/../trace-result/$V/stat/$DATE}
DURATION=${DURATION:-10}
INTERVAL=${INTERVAL:-1}

sync
echo 3 > /proc/sys/vm/drop_caches

pkill sar
pkill iostat
pkill mpstat

set -e
set -u

mkdir -p $OUTDIR
cd $OUTDIR

echo "Start collecting data $DURATION seconds"

sar -A -o sar.out $INTERVAL $DURATION > /dev/null 2>&1 &
iostat  -d -k -x -y $INTERVAL $DURATION > iostat.txt &
mpstat -I CPU $INTERVAL $DURATION > mpstat.txt &

sleep $((DURATION + 3))

sadf -d sar.out -- -d -p > disk.csv; sed -i 's/;/,/g' disk.csv
sadf -d sar.out -- -r > memory.csv; sed -i 's/;/,/g' memory.csv
sadf -d sar.out -- -n DEV > network.csv; sed -i 's/;/,/g' network.csv;
sadf -d sar.out -- -u ALL -P ALL > cpu.csv; sed -i 's/;/,/g' cpu.csv;
sadf -d sar.out -- -I > interrupts.csv; sed -i 's/;/,/g' interrupts.csv;
sar -A -f sar.out > sar_all.dat

# format data

echo "Device,r/s,rkB/s,rrqm/s,%rrqm,r_await,rareq-sz,w/s,wkB/s,wrqm/s,%wrqm,w_await,wareq-sz,d/s,dkB/s,drqm/s,%drqm,d_await,dareq-sz,f/s,f_await,aqu-sz,%util" > io.csv
awk '!/^Linux/' iostat.txt | awk NF | awk '!/^Device/' | tr -s ' ' ',' >> io.csv


echo "Average CPU %usr %nice %sys %iowait %steal %irq %soft %guest %gnice %idle" > summary.txt
cat sar_all.dat | grep Average | grep all | head -n 1 >> summary.txt

echo >> summary.txt
echo "TotalIntrs/sec" >> summary.txt
cat mpstat.txt | tail -n 64 | awk '{sum = 0; for (i = 4; i <= NF; i++){ sum += $i }; print sum;}' | awk '{ total += $1; count++ } END { print total}' >> summary.txt
echo >> summary.txt
cat iostat.txt | grep Device | head -n 1 >> summary.txt
cat iostat.txt | grep $DISK | awk ' FNR==1 { nf=NF} { for(i=1; i<=NF; i++) arr[i]+=$i ; fnr=FNR } END { FS="\t"; for( i=1; i<=nf; i++) printf("%.3f%s", arr[i] / fnr, (i==nf) ? "\n" : FS) }' >> summary.txt

echo >> summary.txt
echo -e "Network\tinterval\ttimestamp\tIFACE\t rxpck/s \t txpck/s \t rxkB/s \t
txkB/s \t rxcmp/s \t txcmp/s \t rxmcst/s \t %ifutil" >> summary.txt
cat network.csv | grep $NIC | awk ' BEGIN { FS = "," } ; FNR==1 { nf=NF} { for(i=1; i<=NF; i++) arr[i]+=$i ; fnr=FNR } END { FS="\t"; for( i=1; i<=nf; i++) printf("%.3f%s", arr[i] / fnr, (i==nf) ? "\n" : FS) }' >> summary.txt

echo "Resut saved: ${OUTDIR}"
