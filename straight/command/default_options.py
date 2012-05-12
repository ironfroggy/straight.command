from straight.command import Option


class VersionOption(Option):
    long = '--version'
    dest = 'version'
    action = 'store_true'

    short_circuit = True

    def run(self, cmd):
        print "Version {0}".format(cmd.version)
