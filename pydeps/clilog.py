# -*- coding: utf-8 -*-
"""
messages for command line interface (cli)
"""
import sys

levels = {"verbose": 0, "debug": 0}


def set_level(name, lvl):
    if name not in levels:
        raise KeyError("unkown level: " + name)
    levels[name] = int(lvl)


def error(*args, file=None, **kwargs):  # pragma: nocover
    """Print an error message and exit.
    """
    if file is None:
        file = sys.stderr

    print("ERROR:", *args, file=file, **kwargs)


def get_effective_level():
    return max(levels.values())


def verbose(n, *args, **kwargs):
    lvl = get_effective_level()
    if not lvl:
        return

    if not isinstance(n, int):
        # this allows the simpler usage cli.verbose(msg)
        args = (n,) + args
        n = 1

    if 0 < lvl <= n:
        print(*args, **kwargs)
