### Installation
```bash
./install.py --no-aws --azure --no-gcp --no-openwhisk --local
```


### Use Environment
```bash
source python-venv/bin/activate
```


### Build Docker Images
The minio-py version of the supplied image is too new (`AttributeError: "Minio" object has no attribute "list_objects_v2"`), so we need to build fitting images.

```bash
tools/build_docker_images.py --deployment local --language python --language-version 3.11
```


### Start Storage
```bash
./sebs.py storage start minio --port 9011 --output-json out_storage.json
jq '.deployment.local.storage = input' config/config_template.json out_storage.json > config/config.json
```


### Benchmark / Experiment
single benchmark:
```bash
./sebs.py benchmark invoke 311.compression test --config config/config.json --verbose
```

all benchmarks:
```bash
BENCHMARKS="110.dynamic-html 120.uploader 210.thumbnailer 220.video-processing 311.compression 411.image-recognition 501.graph-pagerank 502.graph-mst 503.graph-bfs 504.dna-visualisation"
for BENCHMARK in $BENCHMARKS; do ./sebs.py benchmark invoke $BENCHMARK test --config config/config.json --verbose; done
```

prepare config:
```bash
jq '.deployment.local.storage = input | .experiments."perf-cost".benchmark = "210.thumbnailer"' config/config_template.json out_storage.json > config/config.json
```

Experiments:
```bash
# echo "Execute benchmark dynamic-html"
# ./sebs.py experiment invoke perf-cost --config dynamic-html.json --output-dir dynamic-html --output-file run.log
# ./sebs.py experiment process perf-cost --config dynamic-html.json --output-dir dynamic-html --output-file process.log

echo "Execute benchmark uploader"
./sebs.py experiment invoke perf-cost --config uploader.json --output-dir uploader --output-file run.log
./sebs.py experiment process perf-cost --config uploader.json --output-dir uploader --output-file process.log

echo "Execute benchmark thumbnailer"
./sebs.py experiment invoke perf-cost --config thumbnailer.json --output-dir thumbnailer --output-file run.log
./sebs.py experiment process perf-cost --config thumbnailer.json --output-dir thumbnailer --output-file process.log

# echo "Execute benchmark video-processing"
# ./sebs.py experiment invoke perf-cost --config video-processing.json --output-dir video-processing --output-file run.log
# ./sebs.py experiment process perf-cost --config video-processing.json --output-dir video-processing --output-file process.log

echo "Execute benchmark compression"
./sebs.py experiment invoke perf-cost --config compression.json --output-dir compression --output-file run.log
./sebs.py experiment process perf-cost --config compression.json --output-dir compression --output-file process.log

echo "Execute benchmark image-recognition"
./sebs.py experiment invoke perf-cost --config image-recognition.json --output-dir image-recognition --output-file run.log
./sebs.py experiment process perf-cost --config image-recognition.json --output-dir image-recognition --output-file process.log

# echo "Execute benchmark graph-pagerank"
# ./sebs.py experiment invoke perf-cost --config graph-pagerank.json --output-dir graph-pagerank --output-file run.log
# ./sebs.py experiment process perf-cost --config graph-pagerank.json --output-dir graph-pagerank --output-file process.log

# echo "Execute benchmark graph-mst"
# ./sebs.py experiment invoke perf-cost --config graph-mst.json --output-dir graph-mst --output-file run.log
# ./sebs.py experiment process perf-cost --config graph-mst.json --output-dir graph-mst --output-file process.log

echo "Execute benchmark graph-bfs"
./sebs.py experiment invoke perf-cost --config graph-bfs.json --output-dir graph-bfs --output-file run.log
./sebs.py experiment process perf-cost --config graph-bfs.json --output-dir graph-bfs --output-file process.log

# echo "Execute benchmark dna-visualisation"
# ./sebs.py experiment invoke perf-cost --config dna-visualisation.json --output-dir dna-visualisation --output-file run.log
# ./sebs.py experiment process perf-cost --config dna-visualisation.json --output-dir dna-visualisation --output-file process.log
```


### Stop Storage
```bash
./sebs.py storage stop out_storage.json
```


### Remove Containers
```bash
docker rm -f $(docker ps -a --filter "ancestor=spcleth/serverless-benchmarks:build.local.python.3.11" -q)
docker rm -f $(docker ps -a --filter "ancestor=spcleth/serverless-benchmarks:run.local.python.3.11" -q)
```
