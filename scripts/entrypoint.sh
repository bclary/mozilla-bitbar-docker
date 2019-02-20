#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

set -e

source ~/.bashrc

echo "ls -la /"
ls -la /
if [[ -e /test ]]; then
    echo "ls -la /test"
    ls -la /test
fi

WORK_PATH='/builds/taskcluster/'
export ED25519_PRIVKEY="$WORK_PATH/ed25519_private_key"
export OPENPGP_PRIVKEY="$WORK_PATH/openpgp_private_key"
# we're not using livelog yet, set key to something so g-w will start
export LIVELOG_SECRET='not_a_key'

entrypoint.py
cd $HOME
generic-worker new-ed25519-keypair --file $ED25519_PRIVKEY
generic-worker new-openpgp-keypair --file $OPENPGP_PRIVKEY
envsubst < $WORK_PATH/generic-worker.yml.template > $WORK_PATH/generic-worker.yml

# user.Current requires cgo, but cross-compilation doesn't enable cgo
# this works around the issue (see https://github.com/golang/go/issues/14625
# and https://github.com/ksonnet/ksonnet/issues/298)
export USER=root
exec generic-worker run --config $WORK_PATH/generic-worker.yml
