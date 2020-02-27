#!/usr/bin/env bash

set -e

time /builds/taskcluster/script.py$1 '/bin/bash' '-c' './test.py'
