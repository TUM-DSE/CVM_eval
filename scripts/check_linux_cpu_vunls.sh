#!/bin/sh

for file in /sys/devices/system/cpu/vulnerabilities/*; do
  echo -n "`basename $file`: " && cat "$file"
done

