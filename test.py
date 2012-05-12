#!/usr/bin/env python

from __future__ import print_function

import sys
from straight.command import Command, Option


class PrimeOption(Option):

    short = '-p'
    long = '--prime'
    dest = 'prime'
    action = 'store'

    def run(self, cmd):
        n = cmd.args[self.dest]
        if n is not None:
            if self.is_prime(n):
                print("{0} is prime.".format(n))
            else:
                print("{0} is not prime.".format(n))

    def is_prime(self, n):
        n = abs(int(n))
        if n < 2:
            return False
        if n == 2:
            return True
        if not n & 1:
            return False
        for x in range(3, int(n**0.5)+1, 2):
            if n % x == 0:
                return False
        return True


class TestCommand(Command):

    version = "0.1"

    prime = PrimeOption()

    def run(self, arguments):
        super(TestCommand, self).run(arguments)
        
        print()
        print('args:', self.args)
        print('remaining:', self.remaining)


if __name__ == '__main__':
    cmd = TestCommand()
    cmd.run(sys.argv[1:])
