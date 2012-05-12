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
        i = 0
        for i, x in enumerate(xrange(3, int(n**0.5)+1, 2)):
            if i > 0 and i % 100000 == 0:
                print('.', sep='', end='')
                sys.stdout.flush()
            if n % x == 0:
                if i >= 100000:
                    print()
                return False
        if i >= 100000:
            print()
        return True


class SumOption(Option):

    nargs = "?"
    action = "append"
    dest = "numbers"
    coerce = int

    def run(self, cmd):
        if cmd.args[self.dest]:
            total = sum(cmd.args[self.dest])
            print("Total is", total)


class TestCommand(Command):

    version = "0.1"

    summation = SumOption()
    prime = PrimeOption()

    def run(self, arguments):
        super(TestCommand, self).run(arguments)
        
        print()
        print('args:', self.args)
        print('remaining:', self.remaining)


if __name__ == '__main__':
    cmd = TestCommand()
    cmd.run(sys.argv[1:])
