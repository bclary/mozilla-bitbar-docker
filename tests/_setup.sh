#!/usr/bin/env bash

set -e

# TODO: refactor entrypoint.sh to separate scripts so we don't have to ctrl-c entrypoint.sh
adb connect host.docker.internal
entrypoint.sh
