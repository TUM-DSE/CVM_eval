#!/usr/bin/bash

# found in https://github.com/intel/tdx-tools/blob/03c632430f97628180efb8c5e8e04b55e5ae4d4d/attestation/full-disk-encryption/tools/image/scripts/partition#L26
# sudo cryptsetup -v -q luksFormat --type luks2 \
#  --cipher aes-gcm-random --integrity aead --key-size 256 /dev/vdb # removed: --encrypt ( in-place )
# exec inside guest:
# cryptsetup open /dev/vdb crypt-target
#
# integrity
# sudo cryptsetup -v -q luksFormat --type luks2 \              
# --cipher aes-gcm-random --integrity aead --key-size 256 /dev/nvme1n1

# no integrity
sudo cryptsetup -v -q luksFormat --type luks2 \              
  --cipher aes-gcm-random --key-size 256 /dev/nvme1n1
