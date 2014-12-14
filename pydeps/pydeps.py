# -*- coding: utf-8 -*-
import argparse
import os
import pprint
from .py2depgraph import py2dep
from .depgraph2dot import dep2dot
from .dot import dot


def _pydeps(fname, fmt='svg', output=None, verbose=False,
            show=False, show_deps=False, show_dot=False, **kw):
    output = output or (os.path.splitext(fname)[0] + '.' + fmt)
    g = py2dep(fname, debug=verbose, **kw)
    if show_deps:
        print "DEPS:"
        pprint.pprint(g)
    dotsrc = dep2dot(g)
    if show_dot:
        print "DOTSRC:\n", dotsrc
    svg = dot(dotsrc, T=fmt)
    with open(output, 'w') as fp:
        fp.write(svg)
    if show:
        print "firefox " + output
        os.system("firefox " + output)


def pydeps():
    p = argparse.ArgumentParser()
    p.add_argument('fname', help='filename')
    p.add_argument('-v', '--verbose', action='store_true', help="be more verbose")
    p.add_argument('-o', dest='output', metavar="file", help="write output to 'file'")
    p.add_argument('-T', dest='format', default='svg', help="output format (svg|png)")
    p.add_argument('--show', action='store_true', help="call external program to display graph")
    p.add_argument('--show-deps', action='store_true', help="show output of dependency analysis")
    p.add_argument('--show-dot', action='store_true', help="show output of dot conversion")
    p.add_argument('--debug', action='store_true', help="turn on all the show and verbose options")
    p.add_argument('--pylib', action='store_true', help="include python std lib modules")
    p.add_argument('--pylib-all', action='store_true', help="include python all std lib modules (incl. C modules)")

    _args = p.parse_args()
    if _args.verbose:
        print _args
    if _args.debug:
        _args.verbose = True
        _args.show = True
        _args.show_deps = True
        _args.show_dot = True

    _pydeps(
        fname=_args.fname,
        fmt=_args.format,
        output=_args.output,
        verbose=_args.verbose,
        show=_args.show,
        show_deps=_args.show_deps,
        show_dot=_args.show_dot,
        pylib=_args.pylib,
        pylib_all=_args.pylib_all,
    )


if __name__ == '__main__':
    pydeps()
