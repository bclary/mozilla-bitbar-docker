#!/usr/bin/env bash

set -e

# original
#entrypoint.sh

# with timeout (we only need the first parts of entrypoint.sh, not running g-w)
timeout 6 entrypoint.sh
