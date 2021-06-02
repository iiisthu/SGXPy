#!/usr/bin/env bash
DIR="$(dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd ))"
cd $DIR/linux-sgx-driver/

sudo true

echo "Uninstall sgx drivers ..."
service aesmd stop
rmmod graphene_sgx
rmmod isgx
rm -rf "/lib/modules/"`uname -r`"/kernel/drivers/intel/sgx"
/sbin/depmod
/bin/sed -i '/^isgx$/d' /etc/modules

make
make install
/sbin/depmod
/sbin/modprobe isgx
