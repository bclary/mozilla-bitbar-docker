#!/usr/bin/env bash

set -e

/builds/taskcluster/script.py '/bin/bash' '-c' 'for i in {1..10}; do echo "€"; done ## run script 10 times'
