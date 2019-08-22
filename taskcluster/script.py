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

from glob import glob

from mozdevice import ADBAndroid, ADBHost, ADBError, ADBTimeoutError


MAX_NETWORK_ATTEMPTS = 3


def fatal(message, exception=None, retry=True):
    """Emit an error message and exit the process with status
    TBPL_RETRY_EXIT_STATUS this will cause the job to be retried.

    """
    TBPL_RETRY_EXIT_STATUS = 4
    if retry:
        exit_code = TBPL_RETRY_EXIT_STATUS
    else:
        exit_code = 1
    print('TEST-UNEXPECTED-FAIL | bitbar | {}'.format(message))
    if exception:
        print("{}: {}".format(exception.__class__.__name__, exception))
    sys.exit(exit_code)

def get_device_type(device):
    timeout = 10
    device_type = device.shell_output("getprop ro.product.model", timeout=timeout)
    if device_type == "Pixel 2":
        pass
    elif device_type == "Moto G (5)":
        pass
    else:
        fatal("Unknown device ('%s')! Contact Android Relops immediately." % device_type, retry=False)
    return device_type


def enable_charging(device, device_type):
    timeout = 10
    p2_path = "/sys/class/power_supply/battery/input_suspend"
    g5_path = "/sys/class/power_supply/battery/charging_enabled"

    try:
        if device_type == "Pixel 2":
            p2_charging_disabled = (
                device.shell_output(
                    "cat %s 2>/dev/null" % p2_path, timeout=timeout
                ).strip()
                == "1"
            )
            if p2_charging_disabled:
                print("Enabling charging...")
                device.shell_bool(
                    "echo %s > %s" % (0, p2_path), root=True, timeout=timeout
                )
        elif device_type == "Moto G (5)":
            g5_charging_disabled = (
                device.shell_output(
                    "cat %s 2>/dev/null" % g5_path, timeout=timeout
                ).strip()
                == "0"
            )
            if g5_charging_disabled:
                print("Enabling charging...")
                device.shell_bool(
                    "echo %s > %s" % (1, g5_path), root=True, timeout=timeout
                )
        else:
            fatal("Unknown device ('%s')! Contact Android Relops immediately." % device_type, retry=False)
    except (ADBTimeoutError, ADBError) as e:
        fatal("Failed to enable charging. Contact Android Relops immediately.", exception=e, retry=False)


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
        # this can explode if an unknown device, explode now vs in an hour...
        device_type = get_device_type(device)

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

    # enable charging on device if it is disabled
    #   see https://bugzilla.mozilla.org/show_bug.cgi?id=1565324
    enable_charging(device, device_type)

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

    print('script.py exitcode {}'.format(rc))
    return rc

if __name__ == "__main__":
    sys.exit(main())
