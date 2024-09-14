### Installation

#### CVM_eval
```bash
git clone git@github.com:michtum/CVM_eval.git
cd CVM_eval
nix develop
```

```bash
inv build.build-qemu-snp
inv build.build-ovmf-snp
inv build.build-guest-fs-sebs
just setup-linux
```

#### SeBS
```bash
cd benchmarks/sebs
git clone git@github.com:michtum/sebs.git serverless-benchmarks
cd serverless-benchmarks
./install.py --no-aws --azure --no-gcp --no-openwhisk --local
source python-venv/bin/activate
```

Build cointainer images:
```bash
tools/build_docker_images.py --deployment local --language python --language-version 3.11
tools/build_docker_images.py --deployment cvm --language python --language-version 3.11
```



### Environment
```bash
cd CVM_eval/benchmarks/sebs/serverless-benchmarks
sudo nix develop ../../..
source python-venv/bin/activate
```
(sudo needed for CVM)



### Start Storage Container
```bash
./sebs.py storage start minio --port 9011 --output-json out_storage.json
jq '.deployment.local.storage = input' config/config_template.json out_storage.json > config/config.json
```



### Experiments
```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS
do
  jq ".deployment.local.storage = input | .deployment.cvm.storage = input | .experiments.\"perf-cost\".benchmark = \"$BENCHMARK\"" config/config_template.json out_storage.json out_storage.json > config/config.json
  
  ./sebs.py experiment invoke perf-cost --config config/config.json --output-dir $BENCHMARK --output-file run.log
  ./sebs.py experiment process perf-cost --config config/config.json --output-dir $BENCHMARK --output-file process.log
done
```

Results are at e.g. `110.dynamic-html/perf-cost/result.csv`.

- `client_time` is measured at the client and means from invoking the function to getting the result.
- `exec_time` is the runtime of the function code alone (without startup time etc.).

The results are in microseconds.

The connection time is not measured separately.



### Stop Storage
```bash
./sebs.py storage stop out_storage.json
```



### Remove Containers
```bash
docker rm -f $(docker ps -a --filter "ancestor=sebs:run.local.python.3.11" -q)
```



### Appendix
#### Benchmarks
single benchmark:
```bash
./sebs.py benchmark invoke 311.compression test --config config/config.json --verbose
```

all benchmarks:
```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS; do ./sebs.py benchmark invoke $BENCHMARK test --config config/config.json --verbose; done
```
