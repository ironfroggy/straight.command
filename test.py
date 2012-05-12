#!/usr/bin/env python

from __future__ import print_function

import sys
from straight.command import Command, Option


class PrimeOption(Option):

    short = '-p'
    long = '--prime'
    dest = 'prime'
    action = 'store_true'

    def run(self, cmd):
        enable = cmd.args[self.dest]
        if enable is not None:
            cmd.args['total_is_prime'] = self.is_prime(cmd.args['total'])
        else:
            cmd.args['total_is_prime'] = None

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
        total = sum(cmd.args.get(self.dest, []))
        cmd.args['total'] = total


class TestCommand(Command):

    version = "0.1"

    summation = SumOption()
    prime = PrimeOption()
    name = Option(long='--name')

    def run_default(self, total, total_is_prime, **kwargs):
        print('total =', total)
        if total_is_prime is not None:
            print('total is prime?', total_is_prime)
        if kwargs:
            print('remaining args:', kwargs)


if __name__ == '__main__':
    cmd = TestCommand()
    cmd.run(sys.argv[1:])
