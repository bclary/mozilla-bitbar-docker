# mozilla-bitbar-docker
Definition for Mozilla Docker images used at Bitbar

This repository contains the definition for the Docker images used to
run Android Hardware based testing at Bitbar.com.

## Building a Bitbar docker image test zip file

### Accept Android Licenses

The use of the Android SDK and tools requires that the licenses must
be agreed to before they can be used. Your acceptance of the licenses
is recorded in files located in the android-sdk-linux/licenses
directory of your android sdk installation.

Perform a local install of the Android SDK, SDK Tools, Platform Tools
and Build tools matching the versions listed in the Dockerfile and
accept the licenses.

The license agreements are located in the android-sdk-linux/licenses
directory where you installed the Android SDK. Copy these license
files into the licenses directory. The license files will be built
into the final Docker image.

### Build new image test zip file

1. Create the zip file containing the test zip file to be used.

``` bash
./build.sh

```

This will create the following files in the in the `build`
sub-directory of the repository's directory:

* version
* mozilla-docker-CCYYMMDDTHHMMSS.zip
* mozilla-docker-CCYYMMDDTHHMMSS-public.zip

where CCYYMMDDTHHMMSS is the datetime at the time the command was
executed.

`version` contains the datetime the zip file was created.

`mozilla-docker-CCYYMMDDTHHMMSS.zip` contains the contents of the
repository required for the Bitbar mozilla-docker-build project to
create the Docker image including the license files. This file must
**not** be shared publicly.

`mozilla-docker-CCYYMMDDTHHMMSS-public.zip` contains everything in the
`mozilla-docker-CCYYMMDDTHHMMSS.zip` file **without** the license
files. This file **can be** shared publicly.

Execute the [mozilla-docker-build](https://mozilla.testdroid.com/#testing/projects/208991) mozilla bitbar project using the
`mozilla-docker-CCYYMMDDTHHMMSS.zip` file as the test file with
additional parameter `DOCKER_IMAGE_VERSION=CCYYMMDDTHHMMSS`.

### testing

```
pip install pipenv
pipenv install
pipenv shell
pytest taskcluster
```