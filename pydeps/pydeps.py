# -*- coding: utf-8 -*-
"""cli entrypoints.
"""
import ConfigParser
import argparse
import json
import os
import pprint
import sys
import textwrap
import subprocess

from .py2depgraph import py2dep
from .depgraph2dot import dep2dot, cycles2dot
from .dot import dot
from . import __version__
import logging
log = logging.getLogger(__name__)


def _pydeps(**kw):
    fname = kw.pop('fname')
    if kw.get('verbose'):
        def verbose(*args):  # pylint:disable=C0321,W0613,C0111
            print ' '.join(str(a) for a in args)
    else:
        def verbose(*args): pass  # pylint:disable=C0321,W0613,C0111

    output = kw.get('output')
    if not output:
        output = os.path.splitext(fname)[0] + '.' + kw['format']

    g = py2dep(fname, **kw)
    if kw.get('show_deps'):
        verbose("DEPS:")
        pprint.pprint(g)

    if kw.get('show_cycles'):
        dotsrc = cycles2dot(g)
    elif not kw.get('nodot'):
        dotsrc = dep2dot(g)
    else:
        dotsrc = None

    if not kw.get('nodot'):
        if kw.get('show_dot'):
            verbose("DOTSRC:")
            print dotsrc

        svg = dot(dotsrc, T=kw['format'])

        with open(output, 'wb') as fp:
            verbose("Writing output to:", output)
            fp.write(svg)

        if kw.get('show') or kw.get('show_cycles'):
            if kw['display'] is None:
                verbose("Displaying:", output)
                if sys.platform == 'win32':
                    os.startfile(output)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, output])
            else:
                verbose(kw['display'] + " " + output)
                os.system(kw['display'] + " " + output)


# pylint:disable=C0301,R0915
def parse_args(argv=()):
    """Parse command line arguments, and return a dict.
    """
    _p = argparse.ArgumentParser(add_help=False)
    _p.add_argument('--config', help="specify config file", metavar="FILE")
    _p.add_argument('--no-config', help="disable processing of config files", action='store_true')
    _p.add_argument('--version', action='store_true', help='print pydeps version')
    _p.add_argument('-L', '--log', help=textwrap.dedent('''
        set log-level to one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
    '''))
    _args, argv = _p.parse_known_args(argv)

    if _args.log:
        loglevel = getattr(logging, _args.log)
    else:
        loglevel = None

    logging.basicConfig(
        level=loglevel,
        format='%(filename)s:%(lineno)d: %(levelname)s: %(message)s'
    )

    if _args.version:
        print "pydeps v" + __version__
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
        conf = ConfigParser.SafeConfigParser()

        conf.read(config_files)
        try:
            defaults.update(dict(conf.items("pydeps")))
            defaults['exclude'] = [x for x in conf.get('pydeps', 'exclude').split()
                                   if x]
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
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
    p.add_argument('-v', '--verbose', action='count', help="be more verbose (-vv, -vvv for more verbosity)")
    p.add_argument('-o', dest='output', metavar="file", help="write output to 'file'")
    p.add_argument('-T', dest='format', help="output format (svg|png)")
    p.add_argument('--display', help="program to use to display the graph (png or svg file depending on the T parameter)", metavar="PROGRAM")
    # p.add_argument('--show', action='store_true', help="call external program to display graph")
    p.add_argument('--noshow', action='store_true', help="don't call external program to display graph")
    p.add_argument('--show-deps', action='store_true', help="show output of dependency analysis")
    p.add_argument('--show-raw-deps', action='store_true', help="show output of dependency analysis before removing skips")
    p.add_argument('--show-dot', action='store_true', help="show output of dot conversion")
    p.add_argument('--nodot', action='store_true', help="skip dot conversion")
    p.add_argument('--show-cycles', action='store_true', help="show only import cycles")
    p.add_argument('--debug', action='store_true', help="turn on all the show and verbose options")
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
            show_raw_deps=False, verbose=0, include_missing=True,
        )

    _args.show = True

    if _args.noshow:
        _args.show = False
    if _args.nodot and _args.show_cycles:
        print "Can't use --nodot and --show-cycles together"
        sys.exit(1)
    if _args.nodot:
        _args.show_dot = False
    if _args.max_bacon == 0:
        _args.max_bacon = sys.maxint
    if _args.T and not _args.format:
        _args.format = _args.T

    if _args.verbose >= 2:
        print _args
        print
    if _args.debug:
        _args.verbose = True
        _args.show = True
        _args.show_deps = True
        _args.show_dot = True

    return vars(_args)


def externals(pkgname, **kwargs):
    """Return a list of direct external dependencies of ``pkgname``.
    """
    kw = dict(
        T='svg', config=None, debug=False, display=None, exclude=[], externals=True,
        format='svg', max_bacon=2**65, no_config=True, nodot=False,
        noise_level=2**65, noshow=True, output=None, pylib=True, pylib_all=True,
        show=False, show_cycles=False, show_deps=False, show_dot=False,
        show_raw_deps=False, verbose=0, include_missing=True,
    )
    kw.update(kwargs)
    depgraph = py2dep(pkgname, **kw)
    log.info("DEPGRAPH: %s", depgraph)
    pkgname = os.path.splitext(pkgname)[0]

    res = {}
    ext = set()

    for k, src in depgraph.sources.items():
        if k.startswith('_'):
            continue
        if not k.startswith(pkgname):
            continue
        if src.imports:
            imps = [imp for imp in src.imports if not imp.startswith(pkgname)]
            if imps:
                for imp in imps:
                    ext.add(imp.split('.')[0])
                res[k] = imps
    # return res  # debug
    return list(sorted(ext))


def pydeps():
    """Entry point for the ``pydeps`` command.
    """
    _args = parse_args(sys.argv[1:])
    cwd = os.getcwd()
    try:
        fname = os.path.abspath(_args['fname'])
        if not os.path.exists(fname):
            print >>sys.stderr, "No such file:", fname
            sys.exit(1)

        os.chdir(os.path.dirname(fname))
        fname = os.path.basename(fname)

        # curdir = os.getcwd()
        # print "CURDIR:", curdir, os.path.basename(fname)
        # relpath = os.path.relpath(fname, curdir)
        # print "RELPATH:", relpath

        _args['fname'] = fname
        if _args['externals']:
            del _args['fname']
            exts = externals(fname, **_args)
            print json.dumps(exts, indent=4)
        else:
            _pydeps(**_args)
    finally:
        os.chdir(cwd)


if __name__ == '__main__':  # pragma: nocover
    pydeps()
