#!/bin/bash

# TODO: explode if google secrets file isn't present
# TODO: find and replace in entrypoint.sh to define var
#   export GOOGLE_APPLICATION_CREDENTIALS='not_a_key'
sed -i -e 's/export GOOGLE_APPLICATION_CREDENTIALS=\\"not_a_key\\"/export GOOGLE_APPLICATION_CREDENTIALS=\\"key_here\\"/g' scripts/entrypoint.sh

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

# TODO: undo edit of entrypoint.sh