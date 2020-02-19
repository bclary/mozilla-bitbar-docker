#!/usr/bin/env python3

import subprocess
import sys
import time

sys.stdout.write('haha no newline')

# time.sleep(5)

for i in range(1,500):
  print("1111 %s" % i)

sys.stdout.write('haha no newline')

output = subprocess.check_output(
        "base64 /dev/urandom | head -c 10000000",
        stderr=subprocess.STDOUT,
        shell=True)

print(output)

sys.exit(4)

