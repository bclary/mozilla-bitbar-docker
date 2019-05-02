#!/bin/bash

# TODO: explode if google secrets file isn't present

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
