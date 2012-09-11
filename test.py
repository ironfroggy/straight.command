#!/usr/bin/env python

from __future__ import print_function
try:
    unicode
except NameError:
    unicode = str

import sys
from straight.command import Command, Option, SubCommand


class PrimeOption(Option):

    short = '-p'
    long = '--prime'
    dest = 'prime'
    action = 'store_true'
    nargs = 1
    help = "Determine if the number is a prime number."

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

    nargs = "3"
    action = "append"
    dest = "total"
    coerce = int

    def default(self):
        return []

    def run(self, cmd):
        total = sum(cmd.args.get(self.dest, []))
        cmd.args[self.dest] = total


class Rot13Command(Command):

    version = "0.1"

    text = Option(dest='original', coerce=unicode, nargs=1)

    def execute(self, original, **kwargs):
        print(original, "->", original.encode('rot13'))


class Rot13SubCommand(SubCommand):
    name = 'rot13'
    command_class = Rot13Command

class TestCommand(Command):

    version = "0.5"

    summation = SumOption()
    summation2 = SumOption(dest='total2')
    prime = PrimeOption()
    name = Option(long='--name')
    rot13 = Rot13SubCommand()

    def execute(self, total=None, total_is_prime=False, **kwargs):
        print('total =', total)
        if total_is_prime is not None:
            print('total is prime?', total_is_prime)
        print('unused:', kwargs)


if __name__ == '__main__':
    cmd = TestCommand()
    cmd.run(sys.argv[1:])
