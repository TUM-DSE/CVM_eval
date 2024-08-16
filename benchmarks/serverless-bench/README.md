# ServerlessBench



### Setup VM

```bash
nix develop
```

```bash
inv build.build-qemu-snp
inv build.build-ovmf-snp
inv build.build-guest-fs
just setup-linux
```



### Build Images

```bash
inv build.build-guest-fs-serverless-bench
```



### Run Benchmarks

#### NodeJS
```bash
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-node.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Nodejs-hello && node action/hello.js) > /share/result_node_hello.txt'"
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-node.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Nodejs-app && node action/complex.js) > /share/result_node_app.txt'"
```


#### Python
```bash
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-python.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Python-hello && python3 -c '\''from action.hello import main; print(main({\"name\": \"serverless bench\"}))'\'') > /share/result_python_hello.txt'"
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-python.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Python-app && python3 -c '\''from action.__main__ import main; print(main({}))'\'') > /share/result_python_app.txt'"
```


#### Ruby
```bash
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-ruby.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Ruby-hello && ruby -r ./action/hello.rb -e '\''puts main({})'\'') > /share/result_ruby_hello.txt'"
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-ruby.qcow2" --action ssh-cmd --ssh-cmd "sh -c '(cd /opt/Ruby-app && ruby -r ./action/sinatra-web.rb -e '\''puts main({})'\'') > /share/result_ruby_app.txt'"
```

#### C
```bash
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-c.qcow2" --action ssh-cmd --ssh-cmd "sh -c '/opt/C-hello/action/exec > /share/result_c_hello.txt'"
inv vm.start --type amd --size small --image "./build/image/guest-fs-serverless-bench-c.qcow2" --action ssh-cmd --ssh-cmd "sh -c '/opt/C-app/action/exec > /share/result_c_app.txt'"
```
