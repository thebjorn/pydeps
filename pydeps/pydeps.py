# -*- coding: utf-8 -*-
"""cli entrypoints.
"""
from __future__ import print_function
import json
import os
import pprint
import sys
from . import py2depgraph, cli, dot, target
from .depgraph2dot import dep2dot, cycles2dot
import logging
log = logging.getLogger(__name__)


def _pydeps(trgt, **kw):
    # Pass args as a **kw dict since we need to pass it down to functions
    # called, but extract locally relevant parameters first to make the
    # code prettier (and more fault tolerant).
    show_cycles = kw.get('show_cycles')
    nodot = kw.get('nodot')
    output = kw.get('output')
    fmt = kw['format']
    show_svg = kw.get('show')
    if os.getcwd() != trgt.workdir:
        # the tests are calling _pydeps directoy
        os.chdir(trgt.workdir)

    dep_graph = py2depgraph.py2dep(trgt, **kw)

    if kw.get('show_deps'):
        cli.verbose("DEPS:")
        pprint.pprint(dep_graph)

    dotsrc = depgraph_to_dotsrc(dep_graph, show_cycles, nodot)

    if not nodot:
        if kw.get('show_dot'):
            cli.verbose("DOTSRC:")
            print(dotsrc)

        svg = dot.call_graphviz_dot(dotsrc, fmt)

        with open(output, 'wb') as fp:
            cli.verbose("Writing output to:", output)
            fp.write(svg)

        if show_svg or show_cycles:
            dot.display_svg(kw, output)


def depgraph_to_dotsrc(dep_graph, show_cycles, nodot):
    """Convert the dependency graph (DepGraph class) to dot source code.
    """
    if show_cycles:
        dotsrc = cycles2dot(dep_graph)
    elif not nodot:
        dotsrc = dep2dot(dep_graph)
    else:
        dotsrc = None
    return dotsrc


def externals(pkgname, **kwargs):
    """Return a list of direct external dependencies of ``pkgname``.
       Called for the ``pydeps --externals`` command.
    """
    kw = dict(
        T='svg', config=None, debug=False, display=None, exclude=[], externals=True,
        format='svg', max_bacon=2**65, no_config=True, nodot=False,
        noise_level=2**65, noshow=True, output=None, pylib=True, pylib_all=True,
        show=False, show_cycles=False, show_deps=False, show_dot=False,
        show_raw_deps=False, verbose=0, include_missing=True,
    )
    kw.update(kwargs)
    depgraph = py2depgraph.py2dep(pkgname, **kw)
    log.info("DEPGRAPH: %s", depgraph)
    pkgname = os.path.splitext(pkgname)[0]

    res = {}
    ext = set()

    for k, src in list(depgraph.sources.items()):
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


def pydeps(**args):
    """Entry point for the ``pydeps`` command.

       This function should do all the initial parameter and environment
       munging before calling ``_pydeps`` (so that function has a clean
       execution path).
    """
    _args = args if args else cli.parse_args(sys.argv[1:])
    inp = target.Target(_args['fname'])
    log.debug("Target: %r", inp)

    if _args.get('output'):
        _args['output'] = os.path.abspath(_args['output'])
    else:
        _args['output'] = os.path.join(inp.calling_dir,
                                       inp.modpath.replace('.', '_') + '.' + _args['format'])

    with inp.chdir_work():
        _args['fname'] = inp.fname
        _args['isdir'] = inp.is_dir

        if _args['externals']:
            del _args['fname']
            exts = externals(inp.fname, **_args)
            print(json.dumps(exts, indent=4))
        else:
            _pydeps(inp, **_args)        # <=== this is the call you're looking for :-)


if __name__ == '__main__':  # pragma: nocover
    pydeps()
