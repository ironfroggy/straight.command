#!/usr/bin/env python

from distutils.core import setup

setup(name='straight.command',
    version='0.1a1',
    description='A command framework with a plugin architecture',
    author='Calvin Spealman',
    author_email='ironfroggy@gmail.com',
    url='https://github.com/ironfroggy/straight.plugin',
    packages=['straight', 'straight.command'],
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ]
)
