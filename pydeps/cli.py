# -*- coding: utf-8 -*-
"""
command line interface (cli) code.
"""
# pylint: disable=line-too-long
from __future__ import print_function
import argparse

from pydeps.configs import Config
from .arguments import Arguments
# import json
# from .pycompat import configparser
import logging
import os
import sys
import subprocess
import textwrap
from . import __version__


def error(*args, **kwargs):  # pragma: nocover
    """Print an error message and exit.
    """
    kwargs['file'] = sys.stderr
    print("\n\tERROR:", *args, **kwargs)
    if args and args[0].startswith("[Errno 2] No such file or directory"):
        print("\t(Did you forget to include an __init__.py?)")
    sys.exit(1)


#: the (will become) verbose function
verbose = None


def _not_verbose(*args, **kwargs):  # pragma: nocover
    pass


verbose = _not_verbose


def _mkverbose(level):
    def _verbose(n, *args, **kwargs):
        if not isinstance(n, int):  # we're only interested in small integers
            # this allows the simpler usage cli.verbose(msg)
            args = (n,) + args
            n = 1
        if 0 < level <= n:
            print(*args, **kwargs)
    return _verbose


def _find_current_package():
    cwd = os.getcwd()
    while 'setup.py' not in os.listdir(cwd) and cwd != os.path.dirname(cwd):
        cwd = os.path.dirname(cwd)
    if 'setup.py' not in os.listdir(cwd):
        raise Exception("--find-package didn't find setup.py in current, or any parent, directory")
    os.chdir(cwd)
    package_name = subprocess.check_output("python setup.py --name", shell=True).decode('u8').strip()
    return package_name


def base_argparser(argv=()):
    """Initial parser that can set values for the rest of the parsing process.
    """
    global verbose
    verbose = _not_verbose

    _p = argparse.ArgumentParser(add_help=False)
    _p.add_argument('--debug', action='store_true', dest='debug', help="turn on all the show and verbose options (mainly for debugging pydeps itself)")
    _p.add_argument('--config', help="specify config file", metavar="FILE")
    _p.add_argument('--no-config', help="disable processing of config files", action='store_true')
    _p.add_argument('--version', action='store_true', help='print pydeps version')
    _p.add_argument('-L', '--log', help=textwrap.dedent('''
        set log-level to one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
    '''))
    _p.add_argument('--find-package', action='store_true', help="tries to automatically find the name of the current package.")
    _args, argv = _p.parse_known_args(argv)

    if _args.log:
        loglevels = "CRITICAL DEBUG ERROR FATAL INFO WARN"
        if _args.log not in loglevels:  # pragma: nocover
            error('legal values for the -L parameter are:', loglevels)
        loglevel = getattr(logging, _args.log)
    else:
        loglevel = None

    logging.basicConfig(
        level=loglevel,
        format='%(filename)s:%(lineno)d: %(levelname)s: %(message)s'
    )

    if _args.version:  # pragma: nocover
        print("pydeps v" + __version__)
        sys.exit(0)

    return _p, _args, argv  # return parsed and remaining args


def parse_args(argv=()):
    """Parse command line arguments, and return a dict.
    """
    _p, _args, argv = base_argparser(argv)
    find_package = _args.find_package
    config_files = []

    if not _args.no_config:  # process config files
        # extra config file specified with --config <fname> has highest precedence
        if _args.config:
            config_files.append(_args.config)

        # .pydeps file specified in current directory is next
        local_pydeps = os.path.join(os.getcwd(), '.pydeps')
        if os.path.exists(local_pydeps):
            config_files.append(local_pydeps)

        # pydeps.yml file specified in current directory is next
        local_pydeps = os.path.join(os.getcwd(), 'pydeps.yml')
        if os.path.exists(local_pydeps):
            config_files.append(local_pydeps)

        # is there a pyproject.toml file?
        pyproj = os.path.join(os.getcwd(), 'pyproject.toml')
        if os.path.exists(pyproj):
            config_files.append(pyproj)

        # is there a setup.cfg file?
        pyproj = os.path.join(os.getcwd(), 'setup.cfg')
        if os.path.exists(pyproj):
            config_files.append(pyproj)

        # finally the .pydeps file in the the user's homedir
        home = os.environ['USERPROFILE' if sys.platform == 'win32' else 'HOME']
        home_pydeps = os.path.join(home, '.pydeps')
        if os.path.exists(home_pydeps):
            config_files.append(home_pydeps)

    args = Arguments(config_files, debug=True, parents=[_p])

    if not find_package:
        args.add('fname', kind="FNAME:input", help='filename')
    else:
        args.add('--fname', kind="FNAME:input", help='filename')

    args.add('-v', '--verbose', default=0, dest='verbose', action='count', help="be more verbose (-vv, -vvv for more verbosity)")
    args.add('-o', default=None, kind="FNAME:output", dest='output', metavar="file", help="write output to 'file'")
    args.add('-T', default='svg', dest='format', help="output format (svg|png)")
    args.add('--display', kind="FNAME:exe", default=None, help="program to use to display the graph (png or svg file depending on the T parameter)", metavar="PROGRAM")
    args.add('--noshow', '--no-show', action='store_true', default=False, dest='no_show', help="don't call external program to display graph")
    args.add('--show-deps', action='store_true', help="show output of dependency analysis")
    args.add('--show-raw-deps', action='store_true', help="show output of dependency analysis before removing skips")
    args.add('--deps-output', dest='deps_out', default=None, kind="FNAME:output", help="write output of dependency analysis to 'file'")
    args.add('--show-dot', action='store_true', help="show output of dot conversion")
    args.add('--dot-output', dest='dot_out', default=None, kind="FNAME:output", help="write dot code to 'file'")
    args.add('--nodot', '--no-dot', action='store_true', help="skip dot conversion")
    args.add('--no-output', action='store_true', help="don't create .svg/.png file, implies --no-show (-t/-o will be ignored)")
    args.add('--show-cycles', action='store_true', help="show only import cycles")
    args.add('--debug-mf', default=0, type=int, metavar="INT", help="set the ModuleFinder.debug flag to this value")
    args.add('--noise-level', default=200, type=int, metavar="INT", help="exclude sources or sinks with degree greater than noise-level")
    args.add('--max-bacon', default=2, type=int, metavar="INT", help="exclude nodes that are more than n hops away (default=2, 0 -> infinite)")
    args.add('--max-module-depth', default=0, type=int, metavar="INT", help="coalesce deep modules to at most n levels")
    args.add('--pylib', action='store_true', help="include python std lib modules")
    args.add('--pylib-all', action='store_true', help="include python all std lib modules (incl. C modules)")
    args.add('--include-missing', action='store_true', help="include modules that are not installed (or can't be found on sys.path)")
    args.add('-x', '--exclude', default=[], nargs="+", metavar="PATTERN", help="input files to skip (e.g. `foo.*`), multiple file names can be provided")
    args.add('-xx', '--exclude-exact', default=[], nargs="+", metavar="MODULE", help="same as --exclude, except requires the full match. `-xx foo.bar` will exclude foo.bar, but not foo.bar.blob")
    args.add('--only', default=[], nargs="+", metavar="MODULE_PATH", help="only include modules that start with MODULE_PATH")
    args.add('--externals', action='store_true', help='create list of direct external dependencies')
    args.add('--reverse', action='store_true', help="draw arrows to (instead of from) imported modules")
    args.add('--rankdir', default='TB', type=str, choices=['TB', 'BT', 'LR', 'RL'], help="set the direction of the graph, legal values are TB (default, imported modules above importing modules), "
                                                                                         "BT (opposite direction of TB), BT (opposite direction of TB), LR (left-to-right) and RL (right-to-left)")
    args.add('--cluster', action='store_true', help="draw external dependencies as separate clusters")
    args.add('--min-cluster-size', default=0, type=int, metavar="INT", help="the minimum number of nodes a dependency must have before being clustered (default=0)")
    args.add('--max-cluster-size', default=0, type=int, metavar="INT", help="the maximum number of nodes a dependency can have before the cluster is collapsed to a single node (default=0)")
    args.add('--keep-target-cluster', action='store_true', help="draw target module as a cluster")
    args.add('--collapse-target-cluster', action='store_true', help="collapse target module (--keep-target-cluster will be ignored)")
    args.add('--rmprefix', default=[], nargs="+", metavar="PREFIX", help="remove PREFIX from the displayed name of the nodes")
    args.add('--start-color', default=0, type=int, metavar="INT", help="starting value for hue from 0 (red/default) to 360.")

    # args.write_default_config()
    _args = args.parse_args(argv)

    if _args.externals:
        return dict(vars(Config(
            externals=True, fname=_args.fname, max_bacon=10,
            include_missing=True, no_show=True
        )))

    if _args.no_output:
        _args.no_show = True
    _args.show = not _args.no_show
    if _args.no_dot and _args.show_cycles:
        error("Can't use --no=dot and --show-cycles together")  # pragma: nocover
    if _args.no_dot:
        _args.show_dot = False
    if _args.max_bacon == 0:
        _args.max_bacon = sys.maxsize
    if (
        _args.keep_target_cluster
        or _args.min_cluster_size > 0
        or _args.max_cluster_size > 0
        or _args.collapse_target_cluster
    ):
        _args.cluster = True
    if find_package:
        _args.fname = _find_current_package()

    _args.format = getattr(_args, 'format', 'svg')

    verbose = _mkverbose(max(_args.verbose, int(_args.debug)))
    verbose(2, _args, '\n')
    if _args.debug:  # pragma: nocover
        _args.verbose = 1
        _args.show = True
        _args.show_deps = True
        _args.show_dot = True

    return vars(_args)
