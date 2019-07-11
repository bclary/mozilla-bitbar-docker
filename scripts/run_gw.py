#!/usr/bin/env python

import exceptions
import json
import logging
import os
import socket
import subprocess
import sys

script_name = sys.argv[0]

try:
    try:
        import google.cloud.logging
        # setup stackdriver
        stackdriver_client = google.cloud.logging.Client()
        stackdriver_client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        print("%s/WARNING: Stackdriver credentials missing. Stackdriver is not functional." % script_name)
except exceptions.NameError, exceptions.ImportError:
    print("%s/WARNING: Could not import google.cloud.logging! Stackdriver is not functional." % script_name)

# run g-w in a shell with an almost-empty environ
# - print to stdout & stderr
# - log to papertrail

def log_to_pt(message):
    logging.info("%s: %s" % (hostname, message))

scriptvars_json_file = '/builds/taskcluster/scriptvars.json'
gw_config_file = "/builds/taskcluster/generic-worker.yml"
hostname = socket.gethostname()

cmd_str = "generic-worker run --config %s" % gw_config_file
cmd_arr = cmd_str.split(" ")
# testing mode
# cmd_arr = sys.argv[1:]

# load json with env vars if it exists
scriptvars_json = None
if os.path.exists(scriptvars_json_file):
    with open(scriptvars_json_file) as json_file:
        scriptvars_json = json.load(json_file)
else:
    print("%s/INFO: '%s' does not exist." % (script_name, scriptvars_json_file))

# continue until we run a non-superseded task
while True:
    superseded = False
    rc = None

    print("%s/INFO: command to run is: '%s'" % (script_name, " ".join(cmd_arr)))
    # run command
    proc = subprocess.Popen(cmd_arr,
                            env=scriptvars_json,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            )

    while rc == None:
        line = proc.stdout.readline()
        stripped_line = line.rstrip()
        log_to_pt(stripped_line)
        if 'has been superseded' in stripped_line.lower():
            superseded = True
        rc = proc.poll()
    sys.stdout.flush()
    # exit if the rc is non-zero (even if superseded) or if we've processed a real job
    # otherwise consume another task.
    if rc != 0 or not superseded:
        break
    print("%s/INFO: task was superseded, running again..." % script_name)

sys.exit(rc)
