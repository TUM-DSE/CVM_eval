### Installation

#### CVM_eval
```bash
git clone -b sebs git@github.com:TUM-DSE/CVM_eval.git
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
git clone -b normal-benchmarks git@github.com:TUM-DSE/SeBS.git serverless-benchmarks
cd serverless-benchmarks
./install.py --no-aws --azure --no-gcp --no-openwhisk --local
source python-venv/bin/activate
```

Build cointainer images:
```bash
tools/build_docker_images.py --deployment local --language python --language-version 3.11
tools/build_docker_images.py --deployment cvm --language python --language-version 3.11
tools/build_docker_images.py --deployment kata_qemu --language python --language-version 3.11
tools/build_docker_images.py --deployment kata_fc --language python --language-version 3.11
tools/build_docker_images.py --deployment gramine --language python --language-version 3.10
tools/build_docker_images.py --deployment gramine_native --language python --language-version 3.11
tools/build_docker_images.py --deployment native --language python --language-version 3.11
```



### Environment
#### CVM
has to be run on `vislor`/`graham`
```bash
cd CVM_eval/benchmarks/sebs/serverless-benchmarks
sudo nix develop ../../..
source python-venv/bin/activate
```

#### Kata FC
has to be run on `ryan`
```bash
sudo nix-shell -p nerdctl python3Packages.scipy
source python-venv/bin/activate
```



### Start Storage Container
```bash
./sebs.py storage start minio --port 9011 --output-json out_storage.json
jq '.deployment.local.storage = input' config/config_template.json out_storage.json > config/config.json
```



### Experiments
Specify `local`, `cvm`, `kata_qemu`, (`kata_fc`), (`gramine`), `gramine_native`, `native` as `deployment.name` in `config/config_template.json`.

```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS
do
  jq ".deployment.local.storage = input | .deployment.cvm.storage = input | .deployment.kata_qemu.storage = input | .deployment.kata_fc.storage = input | .deployment.gramine.storage = input | .deployment.gramine_native.storage = input | .deployment.native.storage = input | .experiments.\"perf-cost\".benchmark = \"$BENCHMARK\"" config/config_template.json out_storage.json out_storage.json out_storage.json out_storage.json out_storage.json out_storage.json out_storage.json > config/config.json
  
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
docker rm -f $(docker ps -a --filter "ancestor=sebs:run.kata_qemu.python.3.11" -q)
docker rm -f $(docker ps -a --filter "ancestor=sebs:run.gramine.python.3.10" -q)
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
