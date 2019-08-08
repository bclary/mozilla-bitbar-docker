#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import logging
import os
import subprocess
import sys

from distutils.dir_util import copy_tree
from glob import glob

from mozdevice import ADBAndroid, ADBHost, ADBError, ADBTimeoutError


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
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] <test command> (<test command option> ...)',
        description="Wrapper script for tests run on physical Android devices at Bitbar. Runs the provided command wrapped with required setup and teardown.")
    _args, extra_args = parser.parse_known_args()
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

    with open('/builds/taskcluster/scriptvars.json') as scriptvars:
        scriptvarsenv = json.loads(scriptvars.read())
        print('Bitbar test run: https://mozilla.testdroid.com/#testing/device-session/{}/{}/{}'.format(
            scriptvarsenv['TESTDROID_PROJECT_ID'],
            scriptvarsenv['TESTDROID_BUILD_ID'],
            scriptvarsenv['TESTDROID_RUN_ID']))

    env = dict(os.environ)

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
    env['DOCKER_IMAGE_VERSION'] = scriptvarsenv['DOCKER_IMAGE_VERSION']

    if 'HOME' not in env:
        env['HOME'] = '/builds/worker'
        print('setting HOME to {}'.format(env['HOME']))

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

    # run the payload's command
    print(' '.join(extra_args))
    rc = None
    proc = subprocess.Popen(extra_args,
                            env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    while rc == None:
        line = proc.stdout.readline()
        sys.stdout.write(line)
        rc = proc.poll()

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

    # enable charging on device if it is disabled
    #   see https://bugzilla.mozilla.org/show_bug.cgi?id=1565324
    charging_disabled = False
    p2_path = "/sys/class/power_supply/battery/input_suspend"
    g5_path = "/sys/class/power_supply/battery/charging_enabled"
    p2_batt_input_suspended = bool(int(device.shell_output("cat %s" % p2_path)))
    g5_charging_enabled = bool(int(device.shell_output("cat %s" % g5_path)))
    if p2_batt_input_suspended or not g5_charging_enabled:
        charging_disabled = True
    if charging_disabled:
        try:
            timeout = 10
            device_name = device.shell_output("getprop ro.product.model", timeout=timeout)
            print("Enabling charging...")
            if device_name == "Pixel 2":
                device.shell_bool(
                    "echo %s > %s" % (0, p2_path),
                    root=True,
                    timeout=timeout,
                )
            elif device_name == "Moto G (5)":
                device.shell_bool(
                    "echo %s > %s"
                    % (1, g5_path),
                    root=True,
                    timeout=timeout,
                )
            else:
                print(
                    "WARNING: Unknown device! Not sure how to enable charging for device of type '%s'."
                    % device_name
                )
        except (ADBTimeoutError, ADBError) as e:
            print('TEST-UNEXPECTED-FAIL | bitbar | Failed to enable charging. Contact Android Relops immediately.')
            print('{}: {}'.format(e.__class__.__name__, e)
            rc = 1

    print("script.py exitcode {}".format(rc))
    if rc == 0:
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
