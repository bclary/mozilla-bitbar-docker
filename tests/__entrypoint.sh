#!/usr/bin/env bash

set -e

# original
#entrypoint.sh

# with timeout
( entrypoint.sh ) & sleep 10 ; kill $!
