#!/bin/bash

set -e

# TODO: explode if google secrets file isn't present
#   export GOOGLE_APPLICATION_CREDENTIALS='not_a_key'
if [ -e "stackdriver_credentials" ]; then
    creds=`cat stackdriver_credentials`
else
    echo "Please create the 'stackdriver_credentials' file."
    exit 1
fi

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