from straight.command import OptionsPlugin


class VersionOption(OptionsPlugin):
    long = '--version'
    dest = 'version'
    action = 'store_true'
