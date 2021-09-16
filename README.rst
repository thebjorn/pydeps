pydeps
======

.. image:: https://readthedocs.org/projects/pydeps/badge/?version=latest
   :target: https://readthedocs.org/projects/pydeps/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/thebjorn/pydeps/actions/workflows/unit-tests.yml/badge.svg
   :target: https://github.com/thebjorn/pydeps/actions/workflows/unit-tests.yml

.. image:: https://codecov.io/gh/thebjorn/pydeps/branch/master/graph/badge.svg?token=VsYwrSFcJa
   :target: https://codecov.io/gh/thebjorn/pydeps

.. image:: https://pepy.tech/badge/pydeps
   :target: https://pepy.tech/project/pydeps
   :alt: Downloads

Python module dependency visualization.

This package is primarly intended to be used from the command line through the
``pydeps`` command.

.. contents::
   :depth: 2


**Feature requests and bug reports:**

Please report bugs and feature requests on GitHub at
https://github.com/thebjorn/pydeps/issues

How to install
--------------
::

    pip install pydeps

To create graphs with ``pydeps`` you also need to install Graphviz_. Please follow the
installation instructions provided in the Graphviz link (and make
sure the ``dot`` command is on your path).

Usage
------------------
::

    usage: pydeps [-h] [--debug] [--config FILE] [--no-config] [--version]
                  [-L LOG] [-v] [-o file] [-T FORMAT] [--display PROGRAM]
                  [--noshow] [--show-deps] [--show-raw-deps] [--show-dot]
                  [--nodot] [--no-output] [--show-cycles] [--debug-mf INT]
                  [--noise-level INT] [--max-bacon INT] [--pylib] [--pylib-all]
                  [--include-missing] [-x PATTERN [PATTERN ...]]
                  [-xx MODULE [MODULE ...]] [--only MODULE_PATH [MODULE_PATH ...]]
                  [--externals] [--reverse] [--cluster] [--min-cluster-size INT]
                  [--max-cluster-size INT] [--keep-target-cluster]
                  [--rmprefix PREFIX [PREFIX ...]]
                  fname

positional arguments:
  fname                 filename

optional arguments:
  -h, --help                             show this help message and exit
  --config FILE                          specify config file
  --no-config                            disable processing of config files
  --version                              print pydeps version
  -L LOG, --log LOG                      set log-level to one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
  -v, --verbose                          be more verbose (-vv, -vvv for more verbosity)
  -o file                                write output to 'file'
  -T FORMAT                              output format (svg|png)
  --display PROGRAM                      program to use to display the graph (png or svg file depending on the T parameter)
  --noshow                               don't call external program to display graph
  --show-deps                            show output of dependency analysis
  --show-raw-deps                        show output of dependency analysis before removing skips
  --show-dot                             show output of dot conversion
  --nodot                                skip dot conversion
  --no-output                            don't create .svg/.png file, implies --no-show (-t/-o will be ignored)
  --show-cycles                          show only import cycles
  --debug                                turn on all the show and verbose options (mainly for debugging pydeps itself)
  --noise-level INT                      exclude sources or sinks with degree greater than noise-level
  --max-bacon INT                        exclude nodes that are more than n hops away (default=2, 0 -> infinite)
  --pylib                                include python std lib modules
  --pylib-all                            include python all std lib modules (incl. C modules)
  --include-missing                      include modules that are not installed (or can't be found on sys.path)
  --only MODULE_PATH                     only include modules that start with MODULE_PATH, multiple paths can be provided
  --externals                            create list of direct external dependencies
  --reverse                              draw arrows to (instead of from) imported modules
  --cluster                              draw external dependencies as separate clusters
  --min-cluster-size INT                 the minimum number of nodes a dependency must have before being clustered (default=0)
  --max-cluster-size INT                 the maximum number of nodes a dependency can have before the cluster is collapsed to a single node (default=0)
  --keep-target-cluster                  draw target module as a cluster
  --rmprefix PREFIX                      remove PREFIX from the displayed name of the nodes (multiple prefixes can be provided)
  -x PATTERN, --exclude PATTERN          input files to skip (e.g. `foo.*`), multiple patterns can be provided
  --exclude-exact MODULE                 (shorthand -xx MODULE) same as --exclude, except requires the full match. `-xx foo.bar` will exclude foo.bar, but not foo.bar.blob

**Note:** if an option with a variable number of arguments (like ``-x``) is provided
before ``fname``, separe the arguments from the filename with ``--`` otherwise ``fname``
will be parsed as an argument of the option. Example: ``$ pydeps -x os sys -- pydeps``.

You can of course also import ``pydeps`` from Python and use it as a library, look in
``tests/test_relative_imports.py`` for examples.

Example
-------

This is the result of running ``pydeps`` on itself (``pydeps pydeps``):

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps.svg?sanitize=true

(full disclosure: this is for an early version of pydeps)

Notes
-----------

pydeps finds imports by looking for import-opcodes in
python bytecodes (think `.pyc` files). Therefore, only imported files
will be found (ie. pydeps will not look at files in your directory that
are not imported). Additionally, only files that can be found using
the Python import machinery will be considered (ie. if a module is
missing or not installed, it will not be included regardless if it is
being imported). This can be modified by using the ``--include-missing``
flag.

**Displaying the graph:**

To display the resulting ``.svg`` or ``.png`` files, ``pydeps`` by default
calls an appropriate opener for the platform, like ``xdg-open foo.svg``.

This can be overridden with the ``--display PROGRAM`` option, where ``PROGRAM`` is an
executable that can display the image file of the graph.

You can also export the name of such a viewer in either the ``PYDEPS_DISPLAY``
or ``BROWSER`` environment variable, which changes the default behaviour
when ``--display`` is not used.

.pydeps
-------

All options can also be set in a ``.pydeps`` file using ``.ini`` file
syntax (parsable by ``ConfigParser``). Command line options override
options in the ``.pydeps`` file in the current directory, which again
overrides options in the user's home directory
(``%USERPROFILE%\.pydeps`` on Windows and ``${HOME}/.pydeps``
otherwise).

An example .pydeps file::

    [pydeps]
    max_bacon = 2
    no_show = True
    verbose = 0
    pylib = False
    exclude =
        os
        re
        sys
        collections
        __future__

Bacon (Scoring)
---------------

``pydeps`` also contains an Erdős-like scoring function (a.k.a. Bacon
number, from Six degrees of Kevin Bacon
(http://en.wikipedia.org/wiki/Six_Degrees_of_Kevin_Bacon) that lets
you filter out modules that are more than a given number of 'hops'
away from the module you're interested in.  This is useful for finding
the interface a module has to the rest of the world.

To find pydeps' interface to the Python stdlib (less some very common
modules).

::

    shell> pydeps pydeps --show --max-bacon 2 --pylib -x os re types _* enum

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-pylib.svg?sanitize=true

``--max-bacon 2`` (the default) gives the modules that are at most 2
hops away, and modules that belong together have similar colors.
Compare that to the output with the ``--max-bacon=0`` (infinite)
filter:

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-pylib-all.svg?sanitize=true
   :width: 40%

Import cycles
-------------

``pydeps`` can detect and display cycles with the ``--show-cycles``
parameter.  This will _only_ display the cycles, and for big libraries
it is not a particularly fast operation.  Given a folder with the
following contents (this uses yaml to define a directory structure,
like in the tests)::

        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import a

``pydeps relimp --show-cycles`` displays:

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-cycle.svg?sanitize=true


.. _clustering-externals:

Clustering externals
--------------------

Running `pydeps pydeps --max-bacon=4` on version 1.8.0 of pydeps gives the following graph:

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4.svg?sanitize=true

If you are not interested in the internal structure of external modules, you can add the ``--cluster`` flag, which
will collapse external modules into folder-shaped objects::

    shell> pydeps pydeps --max-bacon=4 --cluster

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4-cluster.svg?sanitize=true

To see the internal structure _and_ delineate external modules, use the ``--max-cluster-size`` flag, which controls
how many nodes can be in a cluster before it is collapsed to a folder icon::

    shell> pydeps pydeps --max-bacon=4 --cluster --max-cluster-size=1000

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4-cluster-max1000.svg?sanitize=true

or, using a smaller max-cluster-size::

    shell> pydeps pydeps --max-bacon=4 --cluster --max-cluster-size=3

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4-cluster-max3.svg?sanitize=true

To remove clusters with too few nodes, use the ``--min-cluster-size`` flag::

    shell> pydeps pydeps --max-bacon=4 --cluster --max-cluster-size=3 --min-cluster-size=2

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4-cluster-max3-min2.svg?sanitize=true

In some situations it can be useful to draw the target module as a cluster::

    shell> pydeps pydeps --max-bacon=4 --cluster --max-cluster-size=3 --min-cluster-size=2 --keep-target-cluster

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-18-bacon4-cluster-max3-min2-keep-target.svg?sanitize=true

..and since the cluster boxes include the module name, we can remove those prefixes::

    shell> pydeps pydeps --max-bacon=4 --cluster --max-cluster-size=3 --min-cluster-size=2 --keep-target-cluster --rmprefix pydeps. stdlib_list.

.. image:: https://raw.githubusercontent.com/thebjorn/pydeps/master/docs/_static/pydeps-rmprefix.svg?sanitize=true

Intermediate format
-------------------

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

Version history
---------------

**Version 1.9.14** Thanks to poneill_ for fixing a cryptic error message when
run in a directory without an ``__init__.py`` file.

**Version 1.9.13** Thanks to glumia_ and SimonBiggs_ for improving the documentation.

**Version 1.9.10** ``no_show`` is now honored when placed in ``.pydeps`` file.
Thanks to romain-dartigues_ for the PR.

**Version 1.9.8** Fix for ``maximum recursion depth exceeded`` when using large
frameworks (like ``sympy``).  Thanks to tanujkhattar_ for finding the fix and to
balopat_ for reporting it.

**Version 1.9.7** Check ``PYDEPS_DISPLAY`` and ``BROWSER`` for a program to open
the graph, PR by jhermann_

..
    **Version 1.9.4** pydeps is now available as a pre-commit.com hook thanks to
    a PR by ewen-lbh_

**Version 1.9.1** graphs are now stable on Python 3.x as well -
this was already the case for Py2.7 (thanks to pawamoy_ for reporting
and testing the issue and to kinow_ for helping with testing).

**Version 1.9.0** supports Python 3.8.

**Version 1.8.7** includes a new flag ``--rmprefix`` which lets you remove
prefixes from the node-labels in the graph. The _name_ of the nodes are not effected
so this does not cause merging of nodes, nor does it change coloring - but it
can lead to multiple nodes with the same label (hovering over the node will
give the full name). Thanks to  aroberge_ for the enhancement request.

**Version 1.8.5** With svg as the output format (which is the default),
paths are now hilighted on mouse hover (thanks to tomasito665_ for the
enhancement request).

**Version 1.8.2** incldes a new flag ``--only`` that causes pydeps to
only report on the paths specified::

    shell> pydeps mypackage --only mypackage.a mypackage.b

**Version 1.8.0** includes 4 new flags for drawing external dependencies as
clusters. See clustering-externals_ for examples.
Additionally, the arrowheads now have the color of the source node.

**Version 1.7.3** includes a new flag ``-xx`` or ``--exclude-exact`` which
matches the functionality of the ``--exclude`` flag, except it requires an
exact match, i.e. ``-xx foo.bar`` will exclude foo.bar, but not
``foo.bar.blob`` (thanks to AvenzaOleg_ for the PR).

**Version 1.7.2** includes a new flag, ``--no-output``, which prevents
creation of the .svg/.png file.

**Version 1.7.1** fixes excludes in .pydeps files (thanks to eqvis_
for the bug report).

**Version 1.7.0** The new ``--reverse`` flag reverses the direction
of the arrows in the dependency graph, so they point _to_ the imported
module instead of _from_ the imported module (thanks to goetzk_ for
the bug report and tobiasmaier_ for the PR!).

**Version 1.5.0** Python 3 support (thanks to eight04_ for the PR).

**Version 1.3.4** ``--externals`` will now include modules that
haven't been installed (what ``modulefinder`` calls ``badmodules``).

**Version 1.2.8** A shortcut for finding the direct external dependencies
of a package was added::

    pydeps --externals mypackage

which will print a json formatted list of module names to the screen, e.g.::

    (dev) go|c:\srv\lib\dk-tasklib> pydeps --externals dktasklib
    [
        "dkfileutils"
    ]

which means that the ``dktasklib`` package only depends on the ``dkfileutils``
package.

This functionality is also available programmatically::

    import os
    from pydeps.pydeps import externals
    # the directory that contains setup.py (one level up from actual package):
    os.chdir('package-directory')
    print externals('mypackage')

**Version 1.2.5:** The defaults are now sensible, such that::

    shell> pydeps mypackage

will likely do what you want. It is the same as
``pydeps --show --max-bacon=2 mypackage`` which means display the
dependency graph in your browser, but limit it to two hops (which
includes only the modules that your module imports -- not continuing
down the import chain).  The old default behavior is available with
``pydeps --noshow --max-bacon=0 mypackage``.

Contributing
------------
#. Fork it
#. It is appreciated (but not required) if you raise an issue first: https://github.com/thebjorn/pydeps/issues
#. Create your feature branch (`git checkout -b my-new-feature`)
#. Commit your changes (`git commit -am 'Add some feature'`)
#. Push to the branch (`git push origin my-new-feature`)
#. Create new Pull Request

.. _Graphviz: http://www.graphviz.org/download/
.. _AvenzaOleg: https://github.com/avenzaoleg
.. _eqvis: https://github.com/eqvis
.. _goetzk: https://github.com/goetzk
.. _tobiasmaier: https://github.com/tobiasmaier
.. _eight04: https://github.com/eight04
.. _tomasito665: https://github.com/Tomasito665
.. _aroberge: https://github.com/aroberge
.. _pawamoy: https://github.com/pawamoy
.. _kinow: https://github.com/kinow
.. _ewen-lbh: https://github.com/ewen-lbh
.. _jhermann: https://github.com/jhermann
.. _balopat: https://github.com/balopat
.. _tanujkhattar: https://github.com/tanujkhattar
.. _romain-dartigues: https://github.com/romain-dartigues
.. _glumia: https://github.com/glumia
.. _SimonBiggs: https://github.com/SimonBiggs
.. _poneill: https://github.com/poneill
