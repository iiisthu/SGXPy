#!/usr/bin/env bash

DIR="$(dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd ))"
cd $DIR/sgxpy/

make test
make clean
