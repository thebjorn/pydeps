from pydeps import pydeps
from pydeps.py2depgraph import py2dep


def empty(args):
    args = pydeps.parse_args(['foo', '--no-config'] + args.split())
    args.pop('fname')
    return args


def depgrf(item, args=""):
    return py2dep(item, **empty(args))


def simpledeps(item, args=""):
    return ["%s -> %s" % (a.name, b.name) for a, b in depgrf(item, args)]


# def simpledot(item, args=""):
#     pass
