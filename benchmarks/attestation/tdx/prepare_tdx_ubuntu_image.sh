#!/usr/bin/bash

THIS_DIR=$(dirname "$(readlink -f "$0")")
ROOT_DIR=$THIS_DIR/../../../

# Check if the tdx-ubuntu-guest image exists and if not, create it
if ! [ -f "$ROOT_DIR/build/image/tdx-guest-ubuntu-24.04-generic.qcow2" ]; then
  echo "Creating the ubuntu image from scratch"
  if [ ! -d tdx ]
  then
    git clone https://github.com/canonical/tdx.git
  fi
  cd tdx
  git checkout c77442616fc4220328e24d41c252922cd8354c35
  cd guest-tools/image
  sudo ./create-td-image.sh
  mkdir -p $ROOT_DIR/build/image/
  mv tdx-guest-ubuntu-24.04-generic.qcow2 $ROOT_DIR/build/image/tdx-guest-ubuntu-24.04-generic.qcow2
  cd ../../../
  rm -rf tdx
fi

sudo virt-customize -a "$ROOT_DIR/build/image/tdx-guest-ubuntu-24.04-generic.qcow2" -x \
  --run-command 'apt install just' --ssh-inject root:file:"$ROOT_DIR/nix/ssh_key.pub"
