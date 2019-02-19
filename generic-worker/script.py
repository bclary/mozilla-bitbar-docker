#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import subprocess
import sys

from distutils.dir_util import copy_tree
from glob import glob

from mozdevice import ADBAndroid, ADBHost, ADBError


MAX_NETWORK_ATTEMPTS = 3


def fatal(message):
    """Emit an error message and exit the process with status
    TBPL_RETRY_EXIT_STATUS this will cause the job to be retried.

    """
    # Exit Code 1 until we move to generic-worker since
    # taskcluster-worker reserves 4 for internal worker errors.
    #TBPL_RETRY_EXIT_STATUS = 4
    TBPL_RETRY_EXIT_STATUS = 1
    print('TEST-UNEXPECTED-FAIL | bitbar | {}'.format(message))
    sys.exit(TBPL_RETRY_EXIT_STATUS)

def main():
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                        level=logging.INFO,
                        stream=sys.stdout)

    print('\nBegin script.py')
    with open('/builds/worker/version') as versionfile:
        version = versionfile.read().strip()
    print('\nDockerfile version {}'.format(version))

    taskcluster_debug = '*'

    task_cwd = os.getcwd()
    print('Current working directory: {}'.format(task_cwd))

    artifacts = os.path.join(task_cwd, 'artifacts')
    if not os.path.exists(artifacts):
        fatal('{} does not exist.'.format(artifacts))

    print('Bitbar test run: https://mozilla.testdroid.com/#testing/device-session/{}/{}/{}'.format(
        os.environ['TESTDROID_PROJECT_ID'],
        os.environ['TESTDROID_BUILD_ID'],
        os.environ['TESTDROID_RUN_ID']))

    payload = json.loads(sys.stdin.read())

    print('payload = {}'.format(json.dumps(payload, indent=4)))

    env = dict(os.environ)
    env.update(payload['env'])

    if 'PATH' in os.environ:
        path = os.environ['PATH']
    else:
        path = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin'

    path += ':/builds/worker/android-sdk-linux/tools/bin:/builds/worker/android-sdk-linux/platform-tools'

    env['PATH'] = os.environ['PATH'] = path
    env['NEED_XVFB'] = 'false'
    env['DEVICE_NAME'] = scriptvarsenv['DEVICE_NAME']
    env['ANDROID_DEVICE'] = scriptvarsenv['ANDROID_DEVICE']
    env['DEVICE_SERIAL'] = scriptvarsenv['DEVICE_SERIAL']
    env['HOST_IP'] = scriptvarsenv['HOST_IP']
    env['DEVICE_IP'] = scriptvarsenv['DEVICE_IP']

    if 'HOME' not in env:
        env['HOME'] = '/builds/worker'
        print('setting HOME to {}'.format(env['HOME']))

    if 'TASKCLUSTER_WORKER_TYPE' not in env:
        fatal('TASKCLUSTER_WORKER_TYPE is missing.')

    if 'WORKSPACE' not in env:
        env['WORKSPACE'] = os.path.join(env['HOME'], 'workspace')
        print('setting WORKSPACE to {}'.format(env['WORKSPACE']))
    workspace = env['WORKSPACE']
    if not os.path.exists(workspace):
        print('Creating {}'.format(workspace))
        os.mkdir(workspace)

    # If we are running normal tests we will be connected via usb and
    # there should be only one device connected.  If we are running
    # power tests, the framework will have already called adb tcpip
    # 5555 on the device before it disconnected usb. There should be
    # no devices connected and we will need to perform an adb connect
    # to connect to the device. DEVICE_SERIAL will be set to either
    # the device's serial number or its ipaddress:5555 by the framework.
    try:
        adbhost = ADBHost()
        if env['DEVICE_SERIAL'].endswith(':5555'):
            # Power testing with adb over wifi.
            adbhost.command_output(["connect", env['DEVICE_SERIAL']])
        devices = adbhost.devices()
        print(json.dumps(devices, indent=4))
        if len(devices) != 1:
            fatal('Must have exactly one connected device. {} found.'.format(len(devices)))
    except ADBError as e:
        fatal('{} Unable to obtain attached devices'.format(e))

    try:
        for f in glob('/tmp/adb.*.log'):
            print('\n{}:\n'.format(f))
            with open(f) as afile:
                print(afile.read())
    except Exception as e:
        print('{} while reading adb logs'.format(e))

    print('Connecting to Android device {}'.format(env['DEVICE_SERIAL']))
    try:
        device = ADBAndroid(device=env['DEVICE_SERIAL'])

        # clean up the device.
        device.rm('/data/local/tests', recursive=True, force=True, root=True)
        device.rm('/data/local/tmp/*', recursive=True, force=True, root=True)
        device.rm('/data/local/tmp/xpcb', recursive=True, force=True, root=True)
        device.rm('/sdcard/tests', recursive=True, force=True, root=True)
        device.rm('/sdcard/raptor-profile', recursive=True, force=True, root=True)
    except ADBError as e:
        fatal("{} attempting to clean up device".format(e))

    if taskcluster_debug:
        env['DEBUG'] = taskcluster_debug

    print('environment = {}'.format(json.dumps(env, indent=4)))

    os.chdir(workspace)
    scripturl = payload['context']
    script = os.path.basename(scripturl)
    for attempt in range(MAX_NETWORK_ATTEMPTS):
        try:
            subprocess.check_output(['curl', '-O', scripturl],
                                    stderr=subprocess.STDOUT)
            break
        except subprocess.CalledProcessError as e:
            print('{} during attempt {} to download {}'.format(e, attempt, scripturl))
            if attempt == MAX_NETWORK_ATTEMPTS - 1:
                fatal('Downloading {}'.format(scripturl))

    subprocess.check_output(['chmod', '+x', script],
                            stderr=subprocess.STDOUT)

    # Use a login shell to get the required environment for the unit
    # test scripts to detect sys.executable correctly.  Execute the
    # context script in the directory /builds/worker/workspace.
    args = ['bash', '-l', '-c', ' '.join(payload['command'])]
    print(' '.join(args))
    rc = None
    proc = subprocess.Popen(args,
                            env=env,
                            cwd=workspace,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    while rc == None:
        line = proc.stdout.readline()
        sys.stdout.write(line)
        rc = proc.poll()

    os.chdir(task_cwd)

    # Copy the requested directories to the appropriate
    # location in the task's artifacts directory.
    for artifact in payload['artifacts']:
        artifact_location = os.path.join('artifacts', artifact['name'])
        os.makedirs(artifact_location)
        if os.path.isdir(artifact['path']):
            copy_tree(artifact['path'], artifact_location)
        # Temporarily remove empty files due to
        # https://github.com/taskcluster/taskcluster-worker/issues/341
        for f in glob(os.path.join(artifact_location, '*')):
            if os.path.isfile(f) and os.path.getsize(f) == 0:
                os.unlink(f)

    try:
        if env['DEVICE_SERIAL'].endswith(':5555'):
            device.command_output(["usb"])
            adbhost.command_output(["disconnect", env['DEVICE_SERIAL']])
        adbhost.kill_server()
    except ADBError as e:
        print('{} attempting adb kill-server'.format(e))

    try:
        print('\nnetstat -aop\n%s\n\n' % subprocess.check_output(
            ['netstat', '-aop'],
            stderr=subprocess.STDOUT))
    except subprocess.CalledProcessError as e:
        print('{} attempting netstat'.format(e))

    print('payload.py exitcode {}'.format(rc))
    if rc == 0:
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
