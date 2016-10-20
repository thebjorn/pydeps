# -*- coding: utf-8 -*-
"""
Graphviz interface.
"""

import sys
from subprocess import Popen
import subprocess
import shlex


win32 = sys.platform == 'win32'


def cmd2args(cmd):
    """Prepare a command line for execution by Popen.
    """
    if isinstance(cmd, basestring):
        return cmd if win32 else shlex.split(cmd)
    return cmd


def pipe(cmd, txt):
    """Pipe `txt` into the command `cmd` and return the output.
    """
    return Popen(
        cmd2args(cmd),
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        # shell=win32
    ).communicate(txt)[0]


def dot(src, **kw):
    """Execute the dot command to create an svg output.
    """
    cmd = "dot -T%s" % kw.pop('T', 'svg')
    for k, v in kw.items():
        if v is True:
            cmd += " -%s" % k
        else:
            cmd += " -%s%s" % (k, v)

    if isinstance(src, unicode):
        dotsrc = src.encode('utf-8')
    elif isinstance(src, str):
        dotsrc = src
    else:
        dotsrc = unicode(src).encode('utf-8')

    return pipe(cmd, dotsrc)


# class Digraph(list):
#     def __init__(self, content=None, name='G'):
#         self.name = name
#         if content is not None:
#             if isinstance(content, list):
#                 self.extend(content)
#             elif isinstance(content, basestring):
#                 self.append(content)
#
#     @property
#     def content(self):
#         return ';\n    '.join(self)
#
#     def __eq__(self, other):
#         aval = re.sub(r'\s+', ' ', unicode(self)).strip()
#         bval = re.sub(r'\s+', ' ', unicode(other)).strip()
#         return aval == bval
#
#     def __unicode__(self):
#         return textwrap.dedent(u"""
#            digraph {self.name} {{
#                {self.content}
#            }}
#         """.format(self=self))
#
#     def __str__(self):
#         return unicode(self).encode('utf-8')
#
#     __repr__ = __str__
