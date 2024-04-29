# Network measurement

- [measure.sh](./measure.sh) provides a shell script for evaluation.

## iperf (throughput)
- Example
```
# start the server in the VM
iperf -s -p 7175

# start the client
iperf -c 172.44.0.2 -p 7175 -b 0 -l 1024 -P 8 -u
```
- `-b`: target bandwidth (0: unlimited)
- `-l`: packet size
- `-u`: UDP mode
- `-P`: Number of parallel connections

## ping (latency)
- Example
```
ping 172.44.0.2 -c30 -i 0.1 -s 56
```
- `-c30`: Repeat 30 times
- `-i0.1`: Interval 0.1s
- `-s56`: Packet size 56. Note that this value plus 8 (ICMP header size) is
  the actual packet size.
