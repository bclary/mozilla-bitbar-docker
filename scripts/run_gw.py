#!/usr/bin/env python

import exceptions
import json
import logging
import os
import socket
import subprocess
import sys

try:
    try:
        import google.cloud.logging
        # setup stackdriver
        stackdriver_client = google.cloud.logging.Client()
        stackdriver_client.setup_logging()
    except google.auth.exceptions.DefaultCredentialsError:
        print("WARNING: Stackdriver credentials missing. Stackdriver is not functional.")
except exceptions.NameError, exceptions.ImportError:
    print("WARNING: Could not import google.cloud.logging! Stackdriver is not functional.")

# run g-w in a shell with an almost-empty environ
# - print to stdout & stderr
# - log to papertrail

def log_to_pt(message):
    logging.info("%s: %s" % (hostname, message))

script_name = sys.argv[0]
scriptvars_json_file = '/builds/taskcluster/scriptvars.json'
gw_config_file = "/builds/taskcluster/generic-worker.yml"
hostname = socket.gethostname()

cmd_str = "sudo -u worker generic-worker run --config %s" % gw_config_file
cmd_arr = cmd_str.split(" ")
# testing mode
# cmd_arr = sys.argv[1:]

# load json with env vars if it exists
scriptvars_json = None
if os.path.exists(scriptvars_json_file):
    with open(scriptvars_json_file) as json_file:
        scriptvars_json = json.load(json_file)
else:
    print("INFO: '%s' does not exist." % scriptvars_json_file)

print("%s: command to run is: '%s'" % (script_name, " ".join(cmd_arr)))

# run command
rc = None
proc = subprocess.Popen(cmd_str,
                        env=scriptvars_json,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        shell=True)
while rc == None:
    line = proc.stdout.readline()
    sys.stdout.write(line)
    log_to_pt(line)
    rc = proc.poll()
sys.stdout.flush()
sys.exit(rc)
