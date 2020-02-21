#!/usr/bin/env bash

set -e
set -x

TIME=120

time /builds/taskcluster/script.py${1} '/bin/bash' '-c' "for i in {1..$TIME}; do echo '444'; sleep 1; done ## run script 10 times"
