### Installation
```
./install.py --no-aws --azure --no-gcp --no-openwhisk --local
```

### Build Docker Images
```
tools/build_docker_images.py --deployment local --language python --language-version 3.11
```
The minio-py version of the supplied image is too new (`AttributeError: "Minio" object has no attribute "list_objects_v2"`), so we need to build fitting images.

### Start Storage
```
./sebs.py storage start minio --port 9011 --output-json out_storage.json
jq '.deployment.local.storage = input' config/config.json out_storage.json | sponge config/config.json
```
(requires `nix-shell -p moreutils.out`)

### Start Benchmark
single benchmark:
```
./sebs.py benchmark invoke 311.compression test --config config/config.json --verbose
```

all benchmarks:
```
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS; do ./sebs.py benchmark invoke $BENCHMARK test --config config/config.json --verbose; done
```

### Stop Storage
```
./sebs.py storage stop out_storage.json
```

### Remove Containers
```
docker rm -f $(docker ps -a --filter "ancestor=spcleth/serverless-benchmarks:build.local.python.3.11" -q)
docker rm -f $(docker ps -a --filter "ancestor=spcleth/serverless-benchmarks:run.local.python.3.11" -q)
```
