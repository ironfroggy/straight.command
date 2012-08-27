"""Default options inherited by all commands."""

from __future__ import print_function

from straight.command import Option


class VersionOption(Option):
    long = '--version'
    dest = 'version'
    action = 'store_true'

    help = "Report the current version of a command or subcommand."

    short_circuit = True

    def run(self, cmd):
        print("Version {0}".format(cmd.version))


class Help(Option):
    long = '--help'
    short = '-h'
    dest = 'help'
    action = 'store_true'

    help = "Print this help message."

    short_circuit = True

    def run(self, cmd):
        helps = []
        ml = {}

        def orempty(n, fmt="%s"):
            default = getattr(opt, n, None) or ''
            if default:
                return fmt % (default,)
            return default
        def printhelps(opt, *props, **kwargs):
            indent = kwargs.get('indent', 0)
            print(' ' * indent, end='')
            for prop in props:
                print(help[prop].ljust(ml[prop]), end=' ')

        for opt in cmd.options:
            opt_help = {}

            opt_help['flags'] = ', '.join((orempty('short'), orempty('long'))).strip(', ')
            opt_help['name'] = orempty('name')
            opt_help['default'] = orempty('default', "(%s)")
            opt_help['desc'] = orempty('help')

            for k in opt_help:
                ml[k] = max(ml.get(k, 0), len(opt_help[k]))

            helps.append(opt_help)
        for help in helps:
            printhelps(help, 'flags', 'default', 'name', 'desc')
            print()
        
