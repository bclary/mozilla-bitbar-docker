#!/usr/bin/env python

import os
import json
import subprocess
import sys

# runs a command and:
# - print to stdout & stderr
# - log to papertrail

script_name = sys.argv[0]
scriptvars_json_file = '/builds/taskcluster/scriptvars.json'
gw_config_file = "/builds/taskcluster/generic-worker.yml"

# load json with env vars if it exists
scriptvars_json = None
if os.path.exists(scriptvars_json_file):
    with open(scriptvars_json_file) as json_file:
        scriptvars_json = json.load(json_file)

cmd_str = "generic-worker run --config %s" % gw_config_file
cmd_arr = cmd_str.split(" ")
# testing mode
# cmd_arr = sys.argv[1:]

print("%s: command to run is: '%s'" % (script_name, " ".join(cmd_arr)))

rc = None
proc = subprocess.Popen(cmd_arr,
                        env=scriptvars_json,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        shell=True)
while rc == None:
    line = proc.stdout.readline()
    sys.stdout.write(line)
    # TODO: log to papertrail
    rc = proc.poll()
sys.exit(rc)
