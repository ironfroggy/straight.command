#!/usr/bin/env python

from __future__ import print_function

import sys
from straight.command import Command


class TestCommand(Command):

    version = "0.1"

    def run(self, arguments):
        super(TestCommand, self).run(arguments)
        
        print()
        print('args:', self.args)
        print('remaining:', self.remaining)


if __name__ == '__main__':
    TestCommand().run(sys.argv[1:])
