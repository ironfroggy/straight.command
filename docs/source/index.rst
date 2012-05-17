.. straight.command documentation master file, created by
   sphinx-quickstart on Sun May 13 20:08:44 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Introduction to ``straight.command``
====================================

``straight.command`` is a framework for easily describing commands and their
options, and allowing them to be extended with additional options and even
sub-commands through easy-to-maintain plugins, via the ``straight.plugin`` plugin
loader. Command-line options can be defined in a declarative syntax, which
should be very familiar to many developers.

This is a very early stage in development.


Example
-------

.. code-block:: python

    #!/usr/bin/env python

    from __future__ import print_function
    import sys
    from straight.command import Command, Option, SubCommand

    class List(Command):
        def run_default(self, **extra):
            for line in open(self.parent.args['filename']):
                print(line.strip('\n'))

    class Add(Command):
        new_todo = Option(dest='new_todo', action='append')

        def run_default(self, new_todo, **extra):
            with open(self.parent.args['filename'], 'a') as f:
                for one_todo in new_todo:
                    print(one_todo.strip('\n'), file=f)

    class Todo(Command):
        filename = Option(dest='filename', action='store')       

        list = SubCommand('list', List)
        add = SubCommand('add', Add)

    if __name__ == '__main__':
        Todo().run(sys.argv[1:])


This example shows several commands with declaratively defined options,
including two of them being declared as subcommands of the third.

We can see a number of the features of ``straight.command`` in this example.

Command options are declared with instances of ``Option`` assigned in the
``Command`` subclass, much like the declarative nature of many ORM tools
declaring table columns, so this should be familiar to many developers.

API Documentation
-----------------

* :doc:`modules`
* :doc:`command`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
