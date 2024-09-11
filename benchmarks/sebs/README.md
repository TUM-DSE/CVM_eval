### Installation
#### SeBS
```bash
./install.py --no-aws --azure --no-gcp --no-openwhisk --local
```

Build cointainer images as the minio-py version of the supplied image is too new (`AttributeError: "Minio" object has no attribute "list_objects_v2"`):
```bash
tools/build_docker_images.py --deployment local --language python --language-version 3.11
tools/build_docker_images.py --deployment cvm --language python --language-version 3.11
```


#### CVM_eval
```bash
nix develop
```
```bash
inv build.build-qemu-snp
inv build.build-ovmf-snp
inv build.build-guest-fs-sebs
just setup-linux
```


### Environment
sudo needed for CVM
```bash
cd CVM_eval/benchmarks/sebs/serverless-benchmarks
sudo nix develop ../../..
source python-venv/bin/activate
```


### Start Storage Container
```bash
./sebs.py storage start minio --port 9011 --output-json out_storage.json
jq '.deployment.local.storage = input' config/config_template.json out_storage.json > config/config.json
```


### Benchmarks (optional)
single benchmark:
```bash
./sebs.py benchmark invoke 311.compression test --config config/config.json --verbose
```

all benchmarks:
```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS; do ./sebs.py benchmark invoke $BENCHMARK test --config config/config.json --verbose; done
```


### Experiments (optional)
```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS
do
  jq ".deployment.local.storage = input | .deployment.cvm.storage = input | .experiments.\"perf-cost\".benchmark = \"$BENCHMARK\"" config/config_template.json out_storage.json > config/config.json
  
  ./sebs.py experiment invoke perf-cost --config config/config.json --output-dir $BENCHMARK --output-file run.log
  ./sebs.py experiment process perf-cost --config config/config.json --output-dir $BENCHMARK --output-file process.log
done

rm -rf cache
```

Wichtig!!
- pause muss groß genug sein, um benchmark abzuschließen
- Ergebnis
  - df['client_time'] = df['client_time'] - df['connection_time'] * 1000*1000
  - df['client_time'] /= 10**6
  - --> seconds



### Stop Storage
```bash
./sebs.py storage stop out_storage.json
```


### Remove Containers
```bash
docker rm -f $(docker ps -a --filter "ancestor=sebs:run.local.python.3.11" -q)
```
