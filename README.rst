.. -*- coding: utf-8 -*-


pydeps
======

.. image:: https://readthedocs.org/projects/pydeps/badge/?version=latest
   :target: https://readthedocs.org/projects/pydeps/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/thebjorn/pydeps.svg
   :target: https://travis-ci.org/thebjorn/pydeps


.. image:: https://coveralls.io/repos/thebjorn/pydeps/badge.png
   :target: https://coveralls.io/r/thebjorn/pydeps



Python module dependency visualization. This package installs the ``pydeps``
command, and normal usage will be to use it from the command line. To install::

    pip install pydeps

To create graphs you need to install Graphviz_ (make sure the ``dot``
command is on your path).

.. Note:: to display the resulting `.svg` files, ``pydeps`` by default calls
          ``firefox foo.svg``.  This is can be overridden with the ``--display PROGRAM``
          option, where ``PROGRAM`` is an executable that can display the image file
          of the graph.

.. Note:: Please report bugs and feature requests on GitHub at
          https://github.com/thebjorn/pydeps/issues

This is the result of running ``pydeps`` on itself (``pydeps --show pydeps``):

.. image:: https://dl.dropboxusercontent.com/u/94882440/pydeps.svg

``pydeps`` also contains an Erdős-like scoring function (a.k.a. Bacon
number, from Six degrees of Kevin Bacon
(http://en.wikipedia.org/wiki/Six_Degrees_of_Kevin_Bacon) that lets
you filter out modules that are more than a given number of 'hops'
away from the module you're interested in.  This is useful for finding
the interface a module has to the rest of the world.


To find pydeps' interface to the Python stdlib (less some very common modules).

::

    pydeps pydeps --show --max-bacon 2 --pylib -x os re types _* enum

.. image:: https://dl.dropboxusercontent.com/u/94882440/pydeps-pylib.svg

``--max-bacon 2`` gives the modules that are at most 2 hops away, and modules
that belong together have similar colors.  Compare that to the output
without the ``--max-bacon 2`` filter:

.. image:: https://dl.dropboxusercontent.com/u/94882440/pydeps-pylib-all.svg
   :width: 40%

All options can also be set in a ``.pydeps`` file using ``.ini`` file syntax
(parsable by ``ConfigParser``). Command line options override options in
the ``.pydeps`` file in the current directory, which again overrides options
in the user's home directory (``%USERPROFILE%\.pydeps`` on Windows and
``${HOME}/.pydeps`` otherwise).

``pydeps`` can detect and display cycles with the ``--show-cycles`` parameter.
This will _only_ display the cycles, and for big libraries it is not a
particularly fast operation.  Given a folder with the following contents (this
uses yaml to define a directory structure, like in the tests)::

        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import a

``pydeps relimp --show-cycles`` displays:

.. image:: https://dl.dropboxusercontent.com/u/94882440/pydeps-cycle.svg

An attempt has been made to keep the intermediate formats readable,
eg. the output from ``pydeps --show-deps ..`` looks like this::

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

    usage: pydeps-script.py [-h] [--config FILE] [--no-config] [-v] [-o file]
                        [-T FORMAT] [--display PROGRAM] [--show] [--show-deps]
                        [--show-raw-deps] [--show-dot] [--show-cycles]
                        [--debug] [--noise-level INT] [--max-bacon INT]
                        [--pylib] [--pylib-all] [-x FNAME [FNAME ...]]
                        fname

    positional arguments:
      fname                 filename

    optional arguments:
      -h, --help            show this help message and exit
      --config FILE         specify config file
      --no-config           disable processing of config files
      -v, --verbose         be more verbose (-vv, -vvv for more verbosity)
      -o file               write output to 'file'
      -T FORMAT             output format (svg|png)
      --display PROGRAM     program to use to display the graph (png or svg file
                            depending on the T parameter)
      --show                call external program to display graph
      --show-deps           show output of dependency analysis
      --show-raw-deps       show output of dependency analysis before removing
                            skips
      --show-dot            show output of dot conversion
      --show-cycles         show only import cycles
      --debug               turn on all the show and verbose options
      --noise-level INT     exclude sources or sinks with degree greater than
                            noise-level
      --max-bacon INT       exclude nodes that are more than n hops away
      --pylib               include python std lib modules
      --pylib-all           include python all std lib modules (incl. C modules)
      -x FNAME [FNAME ...], --exclude FNAME [FNAME ...]
                            input files to skip


You can of course import ``pydeps`` from Python (look in the
``tests/test_relative_imports.py`` file for examples.

Contributing
~~~~~~~~~~~~
#. Fork it
#. Create your feature branch (git checkout -b my-new-feature)
#. Commit your changes (git commit -am 'Add some feature')
#. Push to the branch (git push origin my-new-feature)
#. Create new Pull Request


.. _Graphviz: http://www.graphviz.org/Download.php


