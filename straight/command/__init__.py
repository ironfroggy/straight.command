"""A command framework with a plugin architecture.

"""

from __future__ import print_function

import re
from itertools import chain

from straight.plugin import load


class InvalidArgument(ValueError):
    """Raised when an argument is not formatted properly."""


class UnknownArguments(ValueError):
    """Raised when an argment does not match any expected options."""


class _FLAG(object):
    def __init__(self, f=True):
        self.f = f
    def __nonzero__(self):
        return bool(self.f)

_NO_CONST = _FLAG()
_NO_DEFAULT = _FLAG(False)
_NO_VALUE = _FLAG(False)


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
        self.consumers = []
        self.args = {}

        self.loadOptions('straight.command')

        self.options.sort(key=lambda opt: opt.index_for(self))

    def loadOptions(self, namespace):
        """Load options from a plugin namespace, and also from any options
        defined as part of the class body.

        The namespace is used to search all your available python packages
        and locate anything within that namespace. By default, the namespace
        ``"straight.command"`` is used to locate default options, which
        are found in the ``straight.command.default_options`` module.

        Your application can define its own namespace where you can easily
        add options to be located, and if you document this namespace other
        developers can extend your commands with new options by providing
        namespace packages with their own options plugins.
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

        arguments = list(arguments)

        consumers = []
        for opt in self.options:
            if opt.dest:
                default = opt.default
                if hasattr(default, '__call__'):
                    default = default()
                elif default is _NO_DEFAULT:
                    default = _NO_VALUE
                self.args.setdefault(opt.dest, default)
            consumer = Consumer(opt, arguments)
            consumers.append(consumer)

        if not arguments:
            # Parse once, if there are no arguments, to set defaults.
            self._parse_one(consumers)
        while arguments:
            if self._parse_one(consumers):
                continue
            else:
                break

        if arguments:
            raise UnknownArguments(arguments)

    def _parse_one(self, consumers):
        """Allow each option, in order, to consume arguments from the list if
        they match its criteria.
        """

        c = consumers[0].remaining()
        for consumer in consumers:
            if consumer.nargs and consumer.option.parse(consumer, self.args):
                break
        return c != consumers[0].remaining()

    def run(self, arguments):
        """Parse arguments and invoke resulting actions."""

        self.parse(arguments)
        self._run()

    def before_opts(self):
        pass

    def _run(self):
        """If any short_circuit options are matched, and if only one of them
        is matched, it will be run and nothing else. Otherwise, all options
        will be run, then the command's `execute` will be called with
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

        self.before_opts()

        if short_circuit is not None:
            short_circuit.run(self)
        else:
            for opt in self.options:
                if not opt.short_circuit:
                    opt.run(self)

            for opt in self.options:
                if opt.dest and self.args[opt.dest] is _NO_DEFAULT:
                    del self.args[opt.dest]

            self.execute(**self.args)

    def execute(self, **kwargs):
        pass


class Consumer(object):
    """Takes arguments from the argument list, which match the option the
    consumer is assigned to.
    """

    def __init__(self, option, args):
        self.option = option
        self.nargs = option.nargs
        self.args = args

    def __repr__(self):
        return "<Consumer: {0.option} dest={0.option.dest}>".format(self)

    def remaining(self):
        return len(self.args)

    def peek(self):
        return self.args[0]

    def consume(self, mode):
        """Consumes the option from the argument list, and any value it
        accepts.
        """

        args = self.args
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
            coerced_value = self.option.coerce(value)
            args[:consume] = []
            try:
                self.nargs = int(self.nargs) - 1
            except ValueError:
                if self.nargs == '?':
                    self.nargs = 0
            return coerced_value
        except ValueError:
            raise InvalidArgument(value)


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

    
    defaults = (
        ('short', None),
        ('long', None),
        ('dest', None),
        ('nargs', "?"),
        ('action', 'store'),
        ('coerce', (lambda o: o)),
        ('short_circuit', False),
        ('const', _NO_CONST),
        ('default', _NO_DEFAULT),
        ('help', ''),
    )

    __counter = 0
    
    def __init__(self, **kwargs):
        for (defname, defvalue) in self.defaults:
            if defname in kwargs:
                setattr(self, defname, kwargs.pop(defname))
            if not hasattr(self, defname):
                setattr(self, defname, dict(self.defaults)[defname])
        if kwargs:
            raise TypeError("Unexpected initialization parameters: " +
                ', '.join(kwargs.keys()))

        self._check_opts()
        if self.dest is None:
            if self.long:
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
        try:
            int(self.nargs)
        except ValueError:
            if self.nargs not in '?*':
                raise ValueError("nargs must be an integer, ?, or *")

    def parse(self, consumer, ns):
        """Parse the next argument in `args` if it matches this option,
        and execute its `action` accordingly.
        """

        action = getattr(self, 'action_' + self.action)
        mode = None
        try:
            first = consumer.peek()
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
                    action(consumer, ns, mode)
                    return True
                except InvalidArgument as e:
                    # If we are consuming a multi-positional, move on, we're done
                    if not consumer.option.positional:
                        print("Unknown parameter:", e.args[0])
        return False

    def action_store(self, consumer, ns, mode):
        """Action to simple store an expected value."""

        if self.const is _NO_CONST:
            value = consumer.consume(mode)   
        else:
            value = self.const
        if ns[self.dest] is _NO_VALUE:
            ns[self.dest] = value
        else:
            raise InvalidArgument("Received too many values for positional {0}".format(self))

    def action_store_true(self, consumer, ns, mode):
        """Action to store True, and not accept a value."""

        consumer.args.pop(0)
        ns[self.dest] = True

    def action_store_false(self, consumer, ns, mode):
        """Action to store False, and not accept a value."""

        consumer.args.pop(0)
        ns[self.dest] = False

    def action_append(self, consumer, ns, mode):
        """Action to collect all values of the option, if repeated, into a
        single list.
        """

        if ns.get(self.dest) is None:
            ns[self.dest] = []
        value = consumer.consume(mode)
        ns[self.dest].append(value)

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

    def parse(self, consumer, ns):
        """Consumes ALL remaining arguments and prepares to send them to the
        sub-command.
        """

        try:
            first = consumer.peek()
        except IndexError:
            pass
        else:
            if first == self.name:
                consumer.args.pop(0)
                self.subcmd_args = consumer.args[:]
                consumer.args[:] = []

    def run(self, cmd):
        """Runs the subcommand."""

        if self.subcmd_args is not None:
            self.subcmd = self.command_class(parent=cmd)
            self.subcmd.run(self.subcmd_args)
