##!/usr/bin/env bash


# generate the manifest file
# ../sgxpython.py -o . -b ./assert/bower_components/bootstrap/dist/fonts/glyphicons-halflings-regular.woff2 ./assert/bower_components/bootstrap/dist/css/bootstrap.css ./assert/bower_components/bootstrap/dist/css/bootstrap-table.css ./assert/bower_components/jquery/dist/jquery.js ./assert/js/bootstrap.min.js ./assert/js/bootstrap-table.min.js ./assert/js/bootstrap-treeview.js ./index.html ./zjh_performance.png -- httpserver.py


# generate the manifest file(exclude zjh_performance.png)
../sgxpython.py -o . -b ./assert/bower_components/bootstrap/dist/fonts/glyphicons-halflings-regular.woff2 ./assert/bower_components/bootstrap/dist/css/bootstrap.css ./assert/bower_components/bootstrap/dist/css/bootstrap-table.css ./assert/bower_components/jquery/dist/jquery.js ./assert/js/bootstrap.min.js ./assert/js/bootstrap-table.min.js ./assert/js/bootstrap-treeview.js ./index.html -- httpserver.py

# run
# ./python.manifest.sgx `pwd`/httpserver.py


