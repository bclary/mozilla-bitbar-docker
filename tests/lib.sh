#!/usr/bin/env bash

# arguments are: time scriptpy_extension
function timed_echo {
  time /builds/taskcluster/script.py${2} '/bin/bash' '-c' "for i in {1..$1}; do echo 444 \$i; sleep 1; done"
}

# arguments are: time scriptpy_extension
function timed_sleep {
  time /builds/taskcluster/script.py${2} '/bin/bash' '-c' "sleep $1"
}