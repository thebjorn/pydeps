# -*- coding: utf-8 -*-
"""
command line interface (cli) code.
"""
# pylint: disable=line-too-long
from __future__ import print_function
import argparse
from .pycompat import configparser
import logging
import os
import sys
import textwrap
from . import __version__


def error(*args, **kwargs):  # pragma: nocover
    """Print an error message and exit.
    """
    kwargs['file'] = sys.stderr
    print("\n\tERROR:", *args, **kwargs)
    sys.exit(1)


#: the (will become) verbose function
verbose = None


def _not_verbose(*args, **kwargs):  # pragma: nocover
    pass


def _mkverbose(level):
    def _verbose(n, *args, **kwargs):
        if not isinstance(n, int):  # we're only interested in small integers
            # this allows the simpler usage cli.verbose(msg)
            args = (n,) + args
            n = 1
        if 0 < level <= n:
            print(*args, **kwargs)
    return _verbose


def parse_args(argv=()):
    """Parse command line arguments, and return a dict.
    """
    global verbose
    verbose = _not_verbose

    _p = argparse.ArgumentParser(add_help=False)
    _p.add_argument('--config', help="specify config file", metavar="FILE")
    _p.add_argument('--no-config', help="disable processing of config files", action='store_true')
    _p.add_argument('--version', action='store_true', help='print pydeps version')
    _p.add_argument('-L', '--log', help=textwrap.dedent('''
        set log-level to one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
    '''))
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

    defaults = dict(
        T='svg',
        noise_level=200,
        max_bacon=200,
        exclude=[],
        display=None,
    )

    if not _args.no_config:
        home = os.environ['USERPROFILE' if sys.platform == 'win32' else 'HOME']
        config_files = [os.path.join(os.getcwd(), '.pydeps'),
                        os.path.join(home, '.pydeps')]
        if _args.config:
            config_files.insert(0, _args.config)
        conf = configparser.SafeConfigParser()

        conf.read(config_files)
        try:
            defaults.update(dict(conf.items("pydeps")))
            defaults['exclude'] = [x for x in conf.get('pydeps', 'exclude').split()
                                   if x]
        except (configparser.NoOptionError, configparser.NoSectionError):
            pass

        if not defaults['exclude']:
            defaults['exclude'] = []

    p = argparse.ArgumentParser(parents=[_p])

    p.set_defaults(**defaults)
    p.add_argument('fname', help='filename')
    # -v    informative (steps, input/output, statistics)
    # -vv   decision data (computed/converted/replaced values)
    # -vvv  status data (program state at fixed intervals, ie. not in loops)
    # -vvvv execution trace
    p.add_argument('-v', '--verbose', action='count', help="be more verbose (-vv, -vvv for more verbosity)", default=0)
    p.add_argument('-o', dest='output', metavar="file", help="write output to 'file'")
    p.add_argument('-T', dest='format', help="output format (svg|png)")
    p.add_argument('--display', help="program to use to display the graph (png or svg file depending on the T parameter)", metavar="PROGRAM")
    # p.add_argument('--show', action='store_true', help="call external program to display graph")
    p.add_argument('--noshow', action='store_true', help="don't call external program to display graph")
    p.add_argument('--show-deps', action='store_true', help="show output of dependency analysis")
    p.add_argument('--show-raw-deps', action='store_true', help="show output of dependency analysis before removing skips")
    p.add_argument('--show-dot', action='store_true', help="show output of dot conversion")
    p.add_argument('--reverse', action='store_true', help="draw arrows to (instead of from) imported modules")
    p.add_argument('--nodot', action='store_true', help="skip dot conversion")
    p.add_argument('--show-cycles', action='store_true', help="show only import cycles")
    p.add_argument('--debug', action='store_true', help="turn on all the show and verbose options")
    p.add_argument('--debug-mf', default=0, type=int, metavar="INT", help="set the ModuleFinder.debug flag to this value")
    p.add_argument('--noise-level', type=int, metavar="INT", help="exclude sources or sinks with degree greater than noise-level")
    p.add_argument('--max-bacon', type=int, default=2, metavar="INT", help="exclude nodes that are more than n hops away (default=2, 0 -> infinite)")
    p.add_argument('--pylib', action='store_true', help="include python std lib modules")
    p.add_argument('--pylib-all', action='store_true', help="include python all std lib modules (incl. C modules)")
    p.add_argument('--include-missing', action='store_true', help="include modules that are not installed (or can't be found on sys.path)")
    p.add_argument('-x', '--exclude', nargs="+", default=[], metavar="FNAME", help="input files to skip")
    p.add_argument('--externals', action='store_true', help='create list of direct external dependencies')

    _args = p.parse_args(argv)

    if _args.externals:
        return dict(
            T='svg', config=None, debug=False, display=None, exclude=[], externals=True,
            fname=_args.fname, format='svg', max_bacon=10, no_config=False, nodot=False,
            noise_level=200, noshow=True, output=None, pylib=False, pylib_all=False,
            show=False, show_cycles=False, show_deps=False, show_dot=False,
            show_raw_deps=False, verbose=0, include_missing=True, reverse=False,
        )

    _args.show = True

    if _args.noshow:
        _args.show = False
    if _args.nodot and _args.show_cycles:
        error("Can't use --nodot and --show-cycles together")  # pragma: nocover
    if _args.nodot:
        _args.show_dot = False
    if _args.max_bacon == 0:
        _args.max_bacon = sys.maxsize
    if _args.T and not _args.format:
        _args.format = _args.T

    verbose = _mkverbose(max(_args.verbose, int(_args.debug)))
    verbose(2, _args, '\n')
    if _args.debug:  # pragma: nocover
        _args.verbose = 1
        _args.show = True
        _args.show_deps = True
        _args.show_dot = True

    return vars(_args)
