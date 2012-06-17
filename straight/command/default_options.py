"""Default options inherited by all commands."""

from __future__ import print_function

from straight.command import Option


class VersionOption(Option):
    long = '--version'
    dest = 'version'
    action = 'store_true'

    short_circuit = True

    def run(self, cmd):
        print("Version {0}".format(cmd.version))


class Help(Option):
    long = '--help'
    short = '-h'
    dest = 'help'
    action = 'store_true'

    short_circuit = True

    def run(self, cmd):
        helps = []
        ml = {}
        for opt in cmd.options:
            helps.append({
                'flags': ', '.join((opt.short or '', opt.long or '', opt.help or '')).strip(', '),
            })
            ml['flags'] = max(ml.get('flags', 0), len(helps[-1]['flags']))
        for h in helps:
            print(h['flags'].ljust(ml['flags']))
        
