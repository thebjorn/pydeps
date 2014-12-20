pydeps
======

Python Dependency visualization. This package installs the ``pydeps``, and normal
usage will be to use it from the command line.

To create graphs you need to install Graphviz_ (make sure the ``dot`` command is on your path).

.. Note:: to display the resulting `.svg` files, it currently calls ``firefox foo.svg``.
          This is a bug/limitation that will hopefully be fixed soon'ish. I would suggest
          creating a script file called ``firefox`` that redirects to your favorite viewer
          if you can't use ``firefox``. Pull requests are very welcome.

This is the result of running ``pydeps`` on itself (``pydeps --show pydeps``):

.. image:: pydeps.svg

An attempt has been made to keep the intermediate formats readable, eg. the output from
``pydeps --show-deps ..`` looks like this::

    ...
    "pydeps.mf27": {
        "imported_by": [
            "__main__",
            "pydeps.py2depgraph"
        ],
        "kind": "imp.PY_SOURCE",
        "name": "pydeps.mf27",
        "path": "pydeps\\mf27.py"
    },
    "pydeps.py2depgraph": {
        "imported_by": [
            "__main__",
            "pydeps.pydeps"
        ],
        "imports": [
            "pydeps.depgraph",
            "pydeps.mf27"
        ],
        "kind": "imp.PY_SOURCE",
        "name": "pydeps.py2depgraph",
        "path": "pydeps\\py2depgraph.py"
    }, ...

Usage::

    usage: pydeps-script.py [-h] [-v] [-o file] [-T FORMAT] [--show] [--show-deps]
                            [--show-dot] [--debug] [--pylib] [--pylib-all]
                            [-x EXCLUDE [EXCLUDE ...]]
                            fname

    positional arguments:
      fname                 filename

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         be more verbose (-vv, -vvv for more verbosity)
      -o file               write output to 'file'
      -T FORMAT             output format (svg|png)
      --show                call external program to display graph
      --show-deps           show output of dependency analysis
      --show-dot            show output of dot conversion
      --debug               turn on all the show and verbose options
      --pylib               include python std lib modules
      --pylib-all           include python all std lib modules (incl. C modules)
      -x EXCLUDE [EXCLUDE ...], --exclude EXCLUDE [EXCLUDE ...]
                            input files to skip

You can of course import ``pydeps`` from Python (look in the ``tests/test_relative_imports.py`` file
for examples.

.. _Graphviz: http://www.graphviz.org/Download.php

