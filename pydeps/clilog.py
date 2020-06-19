# -*- coding: utf-8 -*-
"""
messages for command line interface (cli)
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import sys

levels = {"verbose": 0, "debug": 0}

def reset_levels():
    set_level("verbose", 0)
    set_level("debug", 0)

def set_level(name, lvl):
    """set the log level for verbose/debug logging"""
    if name not in levels:
        raise KeyError("unkown level: " + name)
    levels[name] = int(lvl)


def error(*args, **kwargs):  # pragma: nocover
    """Print an error message."""
    if kwargs.get("file", None) is None:
        kwargs["file"] = sys.stderr

    print("ERROR:", *args, **kwargs)


def _get_effective_level():
    """by combining debug and verbose,
    figure out which level we have"""
    return max(levels.values())


def verbose(n, *args, **kwargs):
    """log a verbose message with level n"""
    lvl = _get_effective_level()
    if not lvl:
        return

    if not isinstance(n, int):
        # this allows the simpler usage cli.verbose(msg)
        args = (n,) + args
        n = 1

    if 0 < n <= lvl:
        print(*args, **kwargs)
