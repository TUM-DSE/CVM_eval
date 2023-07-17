#!/bin/bash
# SPDX-License-Identifier: MIT

# we cannot use set -Eeuo pipefail because edksetup contains an unused variable
set -Eeo pipefail

build_install_ovmf(){
	GCCVERS="GCC5"
	git clone --single-branch -b snp-latest https://github.com/AMDESE/ovmf $1/ovmf
	pushd $1/ovmf >/dev/null
		git submodule update --init --recursive
	popd >/dev/null
	DIR=$PWD
	pushd $1/ovmf >/dev/null
		git apply --ignore-space-change --ignore-whitespace $DIR/ovmf.patch
		make -C BaseTools
		. ./edksetup.sh --reconfig
		nice build -q --cmd-len=64436 -DDEBUG_ON_SERIAL_PORT -n $(getconf _NPROCESSORS_ONLN) ${GCCVERS:+-t $GCCVERS} -a X64 -p OvmfPkg/OvmfPkgX64.dsc

		mkdir -p $DIR/$1/fds/
		cp -f Build/OvmfX64/DEBUG_$GCCVERS/FV/OVMF_CODE.fd $DIR/$1/fds/
		cp -f Build/OvmfX64/DEBUG_$GCCVERS/FV/OVMF_VARS.fd  $DIR/$1/fds/
	popd >/dev/null
}

build_install_qemu(){
	git clone --single-branch -b "snp-latest" https://github.com/AMDESE/qemu.git $1/qemu
	MAKE="make -j $(getconf _NPROCESSORS_ONLN)"
	DIR=$PWD
	pushd $1/qemu >/dev/null
		git apply $DIR/qemu.patch
		git submodule init
		git submodule update --recursive
		# realpath is needed because meson needs absolute paths
		./configure --target-list=x86_64-softmmu --prefix=$(realpath $1) --disable-werror
		$MAKE
		$MAKE install
	popd >/dev/null
}

if [ $# -lt 1 ]; then
    echo "usage: ./build.sh <dir>"
    exit 1
fi

build_install_qemu $1
build_install_ovmf $1