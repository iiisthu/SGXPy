#!/usr/bin/env bash
DIR="$(dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd ))"
cd $DIR/graphene/

# Install required packages
PACKAGES_TO_INSTALL=""
for PACKAGE in build-essential autoconf gawk bison python3-protobuf libprotobuf-c-dev protobuf-c-compiler
do
    dpkg -s $PACKAGE > /dev/null 2>&1 || PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL $PACKAGE"
done
[[ -z $PACKAGES_TO_INSTALL ]] || sudo apt install $PACKAGES_TO_INSTALL

git submodule update --init
# echo $DIR
pushd Pal/src/host/Linux-SGX/sgx-driver
make <<EOF
$DIR/linux-sgx-driver/
2.1
EOF
([ "$UID" -eq 0 ] && ./load.sh) || sudo ./load.sh
popd

[[ -f ./Pal/src/host/Linux-SGX/signer/enclave-key.pem ]] ||  openssl genrsa -3 -out ./Pal/src/host/Linux-SGX/signer/enclave-key.pem 3072

make SGX=1 DEBUG=1
