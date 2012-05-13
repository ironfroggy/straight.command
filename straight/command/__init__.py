from __future__ import print_function

import re

from straight.plugin import load


class InvalidArgument(ValueError):
    pass

class UnknownArguments(ValueError):
    pass


class Command(object):
    """Collections and parses options to implement a command.

    Commands can collect options defined as attributes of a subclass or
    loaded from one or more namespaces, to be loaded by the plug-in
    loader `straight.command`.

    An instance of Command can be used to `parse()` an argument list,
    or to `run()` the command, which first parses and then carries out
    the task the command was meant for.
    """

    version = "unknown"

    def __init__(self):
        self.options = []
        self.args = {}
        self.remaining = []

        self.loadAttributeOptions()
        self.loadOptionPlugins('straight.command')

        self.options.sort(key=lambda opt: opt.index_for(self))

    def loadOptionPlugins(self, namespace):
        for plugin in load(namespace, subclasses=Option):
            self.options.append(plugin())

    def loadAttributeOptions(self):
        for name in dir(self):
            value = getattr(self, name)
            if isinstance(value, Option):
                self.options.append(value)

    def parse(self, arguments):
        self.remaining = arguments[:]

        if not self.remaining:
            self._parse_defaults(arguments)
        while self.remaining:
            if self._parse_one(arguments):
                continue
            else:
                break
        self._check_unknown()

    def _check_unknown(self):
        if self.remaining:
            raise UnknownArguments(self.remaining)

    def _parse_defaults(self, arguments):
        return self._parse_one(arguments)

    def _parse_one(self, arguments):
        c = len(self.remaining)
        for opt in self.options:
            opt.parse(self.remaining, self.args)
        return c != len(self.remaining)

    def run(self, arguments):
        self.parse(arguments)
        
        short_circuit = None
        for opt in self.options:
            if opt.short_circuit and self.args[opt.dest]:
                if short_circuit is None:
                    short_circuit = opt
                else:
                    raise ValueError("More than one short circuit option!"
                        "Cannot mix {0} and {1}!".format(short_circuit, opt))

        if short_circuit is not None:
            short_circuit.run(self)
        else:
            for opt in self.options:
                if not opt.short_circuit:
                    opt.run(self)

        self.run_default(**self.args)

class Option(object):

    short = None
    long = None
    dest = None
    action = 'store'
    coerce = lambda self, o: o

    short_circuit = False

    __counter = 0
    
    def __init__(self, short=None, long=None, dest=None, action=None, coerce=None):
        self.short = short or self.short
        self.long = long or self.long
        self._check_opts()
        self.action = action or self.action
        if coerce is not None:
            self.coerce = coerce
        if dest:
            self.dest = dest
        elif self.long:
            self.dest = self.long[2:].replace('-', '_') 
        elif self.short:
            self.dest = self.short[1:].replace('-', '_')

        Option.__counter += 1
        self._option_index = self.__counter

    def index_for(self, cmd):
        return self._option_index

    def _check_opts(self):
        if not (self.short or self.long):
            self.positional = True
        else:
            self.positional = False
        if self.short and not re.match(r'-\w[\w\-]*', self.short):
            raise ValueError("Short option must begin with - only.")
        if self.long and not re.match(r'--\w[\w\-]*', self.long):
            raise ValueError("Long option must begin with -- only.")

    def parse(self, args, ns):
        action = getattr(self, 'action_' + self.action)
        mode = None
        self.default(args, ns)
        try:
            first = args[0]
        except IndexError:
            pass
        else:
            if first == self.short:
                mode = 'short'
            elif first.split('=', 1)[0] == self.long:
                mode = 'long'
            elif self.positional:
                mode = 'positional'
            if mode:
                try:
                    action(args, ns, mode)
                except InvalidArgument as e:
                    print("Unknown parameter:", e.args[0])

    def _next_value(self, args, mode):
        consume = 0
        if mode == 'short':
            value = args[:2][1]
            consume = 2
        elif mode == 'long':
            try:
                value = args[0].split('=', 1)
                value = value[1]
            except IndexError:
                raise InvalidArgument(value)
            consume = 1
        elif mode == 'positional':
            value = args[0]
            consume = 1
        try:
            coerced_value = self.coerce(value)
            args[:consume] = []
            return coerced_value
        except ValueError:
            raise InvalidArgument(value)

    def action_store(self, args, ns, mode):
        value = self._next_value(args, mode)   
        if ns[self.dest] is None:
            ns[self.dest] = value
        else:
            raise InvalidArgument("Received too many values for positional {0}".format(self))

    def action_store_true(self, args, ns, mode):
        args.pop(0)
        ns[self.dest] = True

    def action_append(self, args, ns, mode):
        if ns.get(self.dest) is None:
            ns[self.dest] = []
        value = self._next_value(args, mode)
        ns[self.dest].append(value)

    def default(self, args, ns):
        ns.setdefault(self.dest, None)

    def run(self, cmd):
        return NotImplemented


class SubCommand(Option):

    name = None
    command_class = None

    def parse(self, args, ns):
        try:
            first = args[0]
        except IndexError:
            pass
        else:
            if first == self.name:
                subcmd = self.command_class()
                args.pop(0)
                self.subcmd = subcmd
                self.subcmd_args = args[:]
                args[:] = []

    def run(self, cmd):
        self.subcmd.run(self.subcmd_args)
