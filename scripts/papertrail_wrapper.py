#!/usr/bin/env python

import subprocess
import sys

# runs a command and:
# - print to stdout & stderr
# - log to papertrail

if sys.argv[1:]:
    rc = None
    proc = subprocess.Popen(sys.argv[1:],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    while rc == None:
        line = proc.stdout.readline()
        sys.stdout.write(line)
        # TODO: log to papertrail
        rc = proc.poll()
    sys.exit(rc)
else:
    print("ERROR: Please provide a command!")
    sys.exit(1)