import re

from straight.plugin import load


class Command(object):

    version = "unknown"

    def __init__(self):
        self.options = []
        self.args = {}
        self.remaining = []

        self.loadAttributeOptions()
        self.loadOptionPlugins('straight.command')

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

class Option(object):

    short = None
    long = None
    dest = None
    action = 'store'

    short_circuit = False

    __counter = 0
    
    def __init__(self, short=None, long=None, dest=None, action=None):
        self.short = short or self.short
        self.long = long or self.long
        self._check_opts()
        self.action = action or self.action
        if dest:
            self.dest = dest
        elif self.long:
            self.dest = self.long[2:].replace('-', '_') 
        else:
            self.dest = self.short[1:].replace('-', '_')

        self.__counter += 1
        self._option_index = self.__counter

    def _check_opts(self):
        if not (self.short or self.long):
            raise ValueError("Need a -short or --long version of the option.")
        if self.short and not re.match(r'-\w[\w\-]*', self.short):
            raise ValueError("Short option must begin with - only.")
        if self.long and not re.match(r'--\w[\w\-]*', self.long):
            raise ValueError("Long option must begin with -- only.")

    def parse(self, args, ns):
        action = getattr(self, 'action_' + self.action)
        try:
            first = args[0]
        except IndexError:
            pass
        else:
            if args[0] == self.short:
                action(args, ns, 'short')
                return
            elif args[0].split('=', 1)[0] == self.long:
                action(args, ns, 'long')
                return
        self.default(args, ns)

    def action_store(self, args, ns, mode):
        if mode == 'short':
            value = args[:2][1]
            args[:] = args[2:]
        else:
            value = args.pop(0).split('=', 1)[1]
        ns[self.dest] = value

    def action_store_true(self, args, ns, mode):
        args.pop(0)
        ns[self.dest] = True

    def default(self, args, ns):
        ns[self.dest] = None

    def run(self, cmd):
        return NotImplemented
