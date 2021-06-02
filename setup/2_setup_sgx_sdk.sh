#!/usr/bin/env bash
DIR="$(dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd ))"
cd $DIR/linux-sgx/

PACKAGES_TO_INSTALL=""
for PACKAGE in build-essential ocaml automake autoconf libtool wget python libcurl4-openssl-dev protobuf-compiler libprotobuf-dev libprotobuf-c-dev libssl-dev
do
    dpkg -s $PACKAGE > /dev/null || PACKAGES_TO_INSTALL="$PACKAGES_TO_INSTALL $PACKAGE"
done
[[ -z $PACKAGES_TO_INSTALL ]] || sudo apt install $PACKAGES_TO_INSTALL

echo "Installing iclsClient"
mkdir -p /tmp/icls
pushd /tmp/icls
wget http://registrationcenter-download.intel.com/akdlm/irc_nas/11414/iclsClient-1.45.449.12-1.x86_64.rpm
sudo alien --scripts iclsClient-1.45.449.12-1.x86_64.rpm
sudo dpkg -i iclsclient_1.45.449.12-2_amd64.deb
rm iclsClient-1.45.449.12-1.x86_64.rpm
popd
rm -rf /tmp/icls

echo "Installing dynamic-application-loader-host-interface"
pushd /tmp
git clone --depth 1 https://github.com/01org/dynamic-application-loader-host-interface.git
pushd dynamic-application-loader-host-interface
cmake .
make
sudo make install
popd
rm -rf dynamic-application-loader-host-interface
sudo systemctl enable jhi
popd

[[ -d external/ippcp_internal/inc ]] || ./download_prebuilt.sh

make USE_OPT_LIBS=1 DEBUG=1

sudo /opt/intel/sgxpsw/uninstall.sh || true
echo "Installing PSW..."
output=$(./linux/installer/bin/build-installpkg.sh psw)
re='Generated psw installer: ([^'$'\n'']*)'
[[ "$output" =~ $re ]] && installer="${BASH_REMATCH[1]}"

sudo $installer
sudo service aesmd start

sudo ~/sgxsdk/uninstall.sh || true
echo "Installing SDK..."
output=$(./linux/installer/bin/build-installpkg.sh sdk)
re='Generated sdk installer: ([^'$'\n'']*)'
[[ "$output" =~ $re ]] && installer="${BASH_REMATCH[1]}"

sudo $installer <<'EOF'
no
~
EOF
