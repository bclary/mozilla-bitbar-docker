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

CONF_PATH='/builds/taskcluster'
export ED25519_PRIVKEY="$CONF_PATH/ed25519_private_key"
export OPENPGP_PRIVKEY="$CONF_PATH/openpgp_private_key"
# we're not using livelog yet, set key to something so g-w will start
export LIVELOG_SECRET='not_a_key'
export GOOGLE_APPLICATION_CREDENTIALS='not_a_key'
# generic-worker docker hack.
# see https://github.com/taskcluster/generic-worker/issues/151
export USER=root

# write a limited set of environment variables to file
entrypoint.py

cd $HOME
generic-worker new-ed25519-keypair --file $ED25519_PRIVKEY
generic-worker new-openpgp-keypair --file $OPENPGP_PRIVKEY
envsubst < $CONF_PATH/generic-worker.yml.template > $CONF_PATH/generic-worker.yml

# write out key for stackdriver
echo "$GOOGLE_CREDENTIAL" > /etc/google/auth/application_default_credentials.json

mkdir -p /builds/worker/.android/
# bitbar mounts this file into root's homedir, but with g-w adb
# is looking for it worker's homedir
ln -sf /root/.android/adbkey /builds/worker/.android/adbkey || true

# run g-w in a shell with an almost-empty environ
# exec env -i bash -c ". $CONF_PATH/scriptvars.env && generic-worker run --config $CONF_PATH/generic-worker.yml"
run_gw.py
