# -*- coding: utf-8 -*-
import argparse
import os
import pprint
from .py2depgraph import py2dep
from .depgraph2dot import dep2dot
from .dot import dot


def _pydeps(**kw):
    fname = kw.pop('fname')
    if kw.get('verbose'):
        def verbose(*args):
            print ' '.join(str(a) for a in args)
    else:
        def verbose(*args): pass

    output = kw.get('output')
    if not output:
        output = os.path.splitext(fname)[0] + '.' + kw['format']

    g = py2dep(fname, **kw)
    if kw.get('show_deps'):
        verbose("DEPS:")
        pprint.pprint(g)

    dotsrc = dep2dot(g)
    if kw.get('show_dot'):
        verbose("DOTSRC:")
        print dotsrc

    svg = dot(dotsrc, T=kw['format'])

    with open(output, 'w') as fp:
        verbose("Writing output to:", output)
        fp.write(svg)

    if kw.get('show'):
        verbose("firefox " + output)
        os.system("firefox " + output)


def pydeps():
    p = argparse.ArgumentParser()
    p.add_argument('fname', help='filename')
    # -v    informative (steps, input/output, statistics)
    # -vv   decision data (computed/converted/replaced values)
    # -vvv  status data (program state at fixed intervals, ie. not in loops)
    # -vvvv execution trace
    p.add_argument('-v', '--verbose', action='count', help="be more verbose (-vv, -vvv for more verbosity)")
    p.add_argument('-o', dest='output', metavar="file", help="write output to 'file'")
    p.add_argument('-T', dest='format', default='svg', help="output format (svg|png)")
    p.add_argument('--show', action='store_true', help="call external program to display graph")
    p.add_argument('--show-deps', action='store_true', help="show output of dependency analysis")
    p.add_argument('--show-dot', action='store_true', help="show output of dot conversion")
    p.add_argument('--debug', action='store_true', help="turn on all the show and verbose options")
    p.add_argument('--pylib', action='store_true', help="include python std lib modules")
    p.add_argument('--pylib-all', action='store_true', help="include python all std lib modules (incl. C modules)")
    p.add_argument('-x', '--exclude', nargs="+", default=[], help="input files to skip")

    _args = p.parse_args()
    if _args.verbose >= 2:
        print _args
    if _args.debug:
        _args.verbose = True
        _args.show = True
        _args.show_deps = True
        _args.show_dot = True

    _pydeps(**vars(_args))
    #     fname=_args.fname,
    #     fmt=_args.format,
    #     output=_args.output,
    #     verbose=_args.verbose,
    #     show=_args.show,
    #     show_deps=_args.show_deps,
    #     show_dot=_args.show_dot,
    #     pylib=_args.pylib,
    #     pylib_all=_args.pylib_all,
    # )


if __name__ == '__main__':
    pydeps()
