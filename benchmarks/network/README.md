# Network measurement

- [measure.sh](./measure.sh) provides a shell script for evaluation.

## iperf (throughput)
### Server
- Start iperf server
```
# start the server in the VM
iperf -s -p 7175
```

### TCP measurement
- Example
```
# start the client
iperf -c 172.44.0.2 -p 7175 -l 1024 -P 8
```
- `-l`: packet size
- `-P`: Number of parallel connections

### UDP measurement
- Example
```
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
- `-s56`: Data size 56. Note that this value plus 8 (ICMP header size) is
  the actual packet size.

## Note
Network performance largely depends on NIC configurations. (non-exhausitive
but) important things are
- vhost
- Multiqueues
- [UDP RGO](https://developers.redhat.com/articles/2021/11/05/improve-udp-performance-rhel-85)
```
nix run nixpkgs#ethtool -- -K eth1 rx-udp-gro-forwarding on
```

