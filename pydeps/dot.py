# -*- coding: utf-8 -*-
"""
Graphviz interface.
"""
import os
import sys
from subprocess import Popen
import subprocess
import shlex

from . import cli

win32 = sys.platform == 'win32'


def is_unicode(s):
    """Test unicode with py3 support.
    """
    try:
        return isinstance(s, unicode)
    except NameError:
        return False


def to_bytes(s):
    """Convert an item into bytes.
    """
    if isinstance(s, bytes):
        return s
    if isinstance(s, str) or is_unicode(s):
        return s.encode("utf-8")
    try:
        return unicode(s).encode("utf-8")
    except NameError:
        return str(s).encode("utf-8")


def cmd2args(cmd):
    """Prepare a command line for execution by Popen.
    """
    if isinstance(cmd, str):
        return cmd if win32 else shlex.split(cmd)
    return cmd


def pipe(cmd, txt):
    """Pipe `txt` into the command `cmd` and return the output.
    """
    return Popen(
        cmd2args(cmd),
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=win32
    ).communicate(txt)[0]


def dot(src, **kw):
    """Execute the dot command to create an svg output.
    """
    cmd = "dot -T%s" % kw.pop('T', 'svg')
    for k, v in list(kw.items()):
        if v is True:
            cmd += " -%s" % k
        else:
            cmd += " -%s%s" % (k, v)

    return pipe(cmd, to_bytes(src))


def call_graphviz_dot(src, fmt):
    """Call dot command, and provide helpful error message if we
       cannot find it.
    """
    try:
        svg = dot(src, T=fmt)
    except OSError as e:
        if e.errno == 2:
            cli.error("""
               cannot find 'dot'

               pydeps calls dot (from graphviz) to create svg diagrams,
               please make sure that the dot executable is available
               on your path.
            """)
        raise
    return svg


def display_svg(kw, fname):
    """Try to display the svg file on this platform.
    """
    if kw['display'] is None:
        cli.verbose("Displaying:", fname)
        if sys.platform == 'win32':
            os.startfile(fname)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, fname])
    else:
        cli.verbose(kw['display'] + " " + fname)
        os.system(kw['display'] + " " + fname)
