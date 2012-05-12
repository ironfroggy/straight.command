import re

from straight.plugin import load


class Command(object):

    version = "0.1"

    def __init__(self):
        self.options = []
        self.args = {}
        self.remaining = []

        self.loadOptionPlugins('straight.command')

    def loadOptionPlugins(self, namespace):
        for plugin in load(namespace, subclasses=OptionsPlugin):
            self.options.append(plugin())

    def parse(self, arguments):
        self.remaining = arguments[:]

        while self.remaining:
            c = len(self.remaining)
            for opt in self.options:
                opt.parse(self.remaining, self.args)
            if c == len(self.remaining):
                break

class OptionsPlugin(object):

    short = None
    long = None
    dest = None
    action = 'store'
    
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

    def _check_opts(self):
        if not (self.short or self.long):
            raise ValueError("Need a -short or --long version of the option.")
        if self.short and not re.match(r'-\w[\w\-]*', self.short):
            raise ValueError("Short option must begin with - only.")
        if self.long and not re.match(r'--\w[\w\-]*', self.long):
            raise ValueError("Long option must begin with -- only.")

    def parse(self, args, ns):
        action = getattr(self, 'action_' + self.action)
        if args[0] == self.short:
            action(args, ns, 'short')
        if args[0] == self.long:
            action(args, ns, 'long')

    def action_store(self, args, ns, mode):
        if mode == 'short':
            value = args[:2][1]
        else:
            value = args.pop(0).split('=', 1)[1]
        ns[self.dest] = value

    def action_store_true(self, args, ns, mode):
        args.pop(0)
        ns[self.dest] = True
