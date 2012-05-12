#!/usr/bin/env python

import sys
from straight.command import Command

cmd = Command()
cmd.parse(sys.argv[1:])

print 'args:', cmd.args
print 'remaining:', cmd.remaining
