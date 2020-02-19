#!/usr/bin/env bash

set -e

/builds/taskcluster/script.py '/bin/bash' '-c' 'for i in {1..45}; do echo "444"; sleep 1; done ## run script 10 times'
