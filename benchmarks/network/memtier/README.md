# Memtier-benchmark (redis / memcached)

## Start server
```
nix-shell

just run-redis
just run-memcached
```

## Memtier-benchmark
```
memtier_benchmark --host=172.44.0.2 -p 6379 --protocol=redis // redis
memtier_benchmark --host=172.44.0.2 -p 6379 --protocol=memcache_text // memcached
```
- `-t`: number of threads (default: 4)
- `-c`: number of clients per thread (default: 50)
- `--pipeline`: number of concurrent piplined request (default: 1)
