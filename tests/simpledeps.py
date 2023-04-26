import pydeps.cli
from pydeps import pydeps
from pydeps.py2depgraph import py2dep
from pydeps.target import Target


def empty(args="", **kw):
    args = pydeps.cli.parse_args(['foo', '--no-config'] + args.split())
    args.pop('fname')
    args.update(kw)
    return args


def depgrf(item, args=""):
    t = Target(item)
    # print("TARGET:", t)
    with t.chdir_work():
        res = py2dep(t, **empty(args))
        # print("DEPGRPH:", res)
        return res


def simpledeps(item, args=""):
    return {"%s -> %s" % (a.name, b.name) for a, b in depgrf(item, args)}
