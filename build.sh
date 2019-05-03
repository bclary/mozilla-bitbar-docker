#!/bin/bash

set -e

sd_cred_file="stackdriver_credentials.json"
# explode if google secrets file isn't present
if [ ! -e "$sd_cred_file" ]; then
    echo "Please create the '$sd_cred_file' file."
    echo "The secret lives in ssh://gitolite3@git-internal.mozilla.org/relops/gpg.git"
    echo "at service_account_keys/bitbar-docker-log-writer@bitbar-devicepool.iam.gserviceaccount.com.json.gpg"
    exit 1
fi
creds=`cat $sd_cred_file`

# find and replace in entrypoint.sh to define var
# - should work on gnu and bsd sed
sed -i.bak "s/export GOOGLE_APPLICATION_CREDENTIALS='not_a_key'/export GOOGLE_APPLICATION_CREDENTIALS='$creds'/g" scripts/entrypoint.sh

workdir=$(dirname $0)
pushd $workdir

if [[ ! -e build ]]; then
    mkdir build
fi

datelabel=$(date  +%Y%m%dT%H%M%S)
echo $datelabel > version
zip -r build/mozilla-docker-$datelabel.zip . -x@zipexclude.lst
zip -r build/mozilla-docker-$datelabel-public.zip . -x@zipexclude.lst

popd

# undo edit of entrypoint.sh
mv scripts/entrypoint.sh.bak scripts/entrypoint.sh