#!/usr/bin/env bash

set -x

OUT=${1:-out.svg}

lstopo --merge --no-legend --no-io --ignore pci --ignore net --of svg > $OUT
