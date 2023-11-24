#!/bin/sh

sudo modprobe msr

TDX_ENABLED=`sudo rdmsr 0x1401 -f 11:11`
TDX_KEY_BIT=`sudo rdmsr -f 39:36 0x982`
TDX_NUM_KEY=`sudo rdmsr -f 63:32 0x87`
TME_ENABLED=`sudo rdmsr -f 1:1 0x982`
TME_BYPASS_ENABLED=`sudo rdmsr -f 31:31 0x982`
TME_MAX_KEY=`sudo rdmsr -f 50:36 0x981`

echo "TDX enabled: $TDX_ENABLED"
echo "TDX key BIT: $TDX_KEY_BIT"
echo "TDX number of TDX key: $TDX_NUM_KEY"

echo "TME enabled: $TME_ENABLED"
echo "TME bypass enabled: $TME_BYPASS_ENABLED"
echo "TME max keys: $TME_MAX_KEY"
