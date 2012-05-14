from __future__ import print_function

import re
from itertools import chain

from straight.plugin import load


class InvalidArgument(ValueError):
    """Raised when an argument is not formatted properly."""


class UnknownArguments(ValueError):
    """Raised when an argment does not match any expected options."""


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

    def __init__(self, parent=None):
        self.parent = parent
        self.options = []
        self.args = {}
        self.remaining = []

        self.loadOptions('straight.command')

        self.options.sort(key=lambda opt: opt.index_for(self))

    def loadOptions(self, namespace):
        """Load options from a plugin namespace, and also from any options
        defined as part of the class body.
        """

        from_attributes = self._getAttributes(Option)
        from_plugins = self._getPlugins(namespace, Option)
        self.options.extend(from_attributes)
        self.options.extend(from_plugins)

    def _getPlugins(self, namespace, cls):
        """Utility to load and instansiate a set of plugins."""

        for plugin in load(namespace, subclasses=cls):
            yield plugin()

    def _getAttributes(self, cls):
        """Utility to locate class-defined options."""

        for name in dir(self):
            value = getattr(self, name)
            if isinstance(value, cls):
                yield value

    def parse(self, arguments):
        """Parse all known arguments, populating the `args` dict."""

        self.remaining = arguments[:]

        if not self.remaining:
            # Parse once, if there are no arguments, to set defaults.
            self._parse_one(arguments)
        while self.remaining:
            if self._parse_one(arguments):
                continue
            else:
                break
        self._check_unknown()

    def _check_unknown(self):
        """Be default, unknown arguments are rejected and parsing
        terminated.
        """

        if self.remaining:
            raise UnknownArguments(self.remaining)

    def _parse_one(self, arguments):
        """Allow each option, in order, to consume arguments from the list if
        they match its criteria.
        """

        c = len(self.remaining)
        for opt in self.options:
            opt.parse(self.remaining, self.args)
        return c != len(self.remaining)

    def run(self, arguments):
        """Parse arguments and invoke resulting actions."""

        self.parse(arguments)
        self._run(arguments)

    def _run(self, arguments):
        """If any short_circuit options are matched, and if only one of them
        is matched, it will be run and nothing else. Otherwise, all options
        will be run, then the command's `run_default` will be called with
        the resulting parsed arguments as keyword arguments.
        """

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

    def run_default(self, **kwargs):
        pass

class Option(object):
    """Defines a single option a command can take.

    Options can define a short (-s) or long (--long) or be positional.
    
    Initialization parameters:

    - `short` an optional single-dash (-s) argument to accept
    - `long` an optional single-dash (--long) argument to accept
    - `dest` the name to save any resulting values to
    - `action` the action to peform if an option is matched
      Can be one of:
        `store` to accept one value to store 
        `append` to accept multiple values to store in a list 
        `store_true` to store True if matched
        `store_false` to store False if matched
    - `coerce` a callable accepting the given string value for an option, and
      returning a value of a correct type
    - `short_circuit` true if the option can be the only one run
    """

    _DEFAULT = {
        'append': list,
    }

    short = None
    long = None
    dest = None
    action = 'store'
    coerce = lambda self, o: o
    short_circuit = False

    __counter = 0
    
    def __init__(self, short=None, long=None, dest=None, action=None, coerce=None, short_circuit = None):
        self.short = short or self.short
        self.long = long or self.long
        self._check_opts()
        self.action = action or self.action
        if short_circuit is not None:
            self.short_circuit = short_circuit
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
        """Provides the index number to order an option in a command.

        Defaults the order they were created.        
        """

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
        """Parse the next argument in `args` if it matches this option,
        and execute its `action` accordingly.
        """

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
        """Consumes the option from the argument list, and any value it
        accepts.
        """

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
        """Action to simple store an expected value."""

        value = self._next_value(args, mode)   
        if ns[self.dest] is None:
            ns[self.dest] = value
        else:
            raise InvalidArgument("Received too many values for positional {0}".format(self))

    def action_store_true(self, args, ns, mode):
        """Action to store True, and not accept a value."""

        args.pop(0)
        ns[self.dest] = True

    def action_store_false(self, args, ns, mode):
        """Action to store False, and not accept a value."""

        args.pop(0)
        ns[self.dest] = False

    def action_append(self, args, ns, mode):
        """Action to collect all values of the option, if repeated, into a
        single list.
        """

        if ns.get(self.dest) is None:
            ns[self.dest] = []
        value = self._next_value(args, mode)
        ns[self.dest].append(value)

    def default(self, args, ns):
        ns.setdefault(self.dest, self._DEFAULT.get(self.action, lambda:None)())

    def run(self, cmd):
        """An Option subclass can define `run()` to invoke some behavior
        during the commands run-phase, if the option had been matched.
        """

        return NotImplemented


class SubCommand(Option):
    """Implements a "sub-command option", which consumes all the remaining
    options and delegates them to another Command.

    Requires a name and a Command sub-class to delegate to.
    """

    name = None
    command_class = None

    def __init__(self, name=None, command_class=None, *args, **kwargs):
        super(SubCommand, self).__init__(*args, **kwargs)
        if name:
            self.name = name
        if command_class:
            self.command_class = command_class
        self.subcmd = None
        self.subcmd_args = None

        if not self.name or not self.command_class:
            raise TypeError("{0.__class__.__name__} requires both "
                "`name` and `command_class`.".format(self))

    def parse(self, args, ns):
        """Consumes ALL remaining arguments and prepares to send them to the
        sub-command.
        """

        try:
            first = args[0]
        except IndexError:
            pass
        else:
            if first == self.name:
                args.pop(0)
                self.subcmd_args = args[:]
                args[:] = []

    def run(self, cmd):
        """Runs the subcommand."""

        if self.subcmd_args is not None:
            self.subcmd = self.command_class(parent=cmd)
            self.subcmd.run(self.subcmd_args)
