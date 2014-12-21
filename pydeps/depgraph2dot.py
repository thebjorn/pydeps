"""
# Based on original code, Copyright 2004 Toby Dickenson,
# with changes 2014 (c) Bjorn Pettersen
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import json
import sys
import getopt
import imp
from . import colors
from .render_context import RenderContext


class PyDepGraphDot(object):
    def __init__(self, colored=True):
        self.colored = colored

    def render(self, depgraph, ctx):
        with ctx.graph():
            visited = set()

            for a, b in depgraph:
                # b imports a
                ctx.write_rule(a.name, b.name,
                               weight=depgraph.proximity_metric(a, b),
                               minlen=depgraph.dissimilarity_metric(a, b))
                visited.add(a)
                visited.add(b)

            for src in visited:
                bg, fg = depgraph.get_colors(src)
                ctx.write_node(src.name, label=src.label,
                               fillcolor=colors.rgb2css(bg),
                               fontcolor=colors.rgb2css(fg))

        return ctx.text()

    def filter_modules(self, module_name, kind):
        """Return true if this module is interesting and should be drawn.
           Return false if it should be completely omitted. This is a
           default policy - please override.
        """
        if module_name in ('os', 'sys', 'qt', 'time', '__future__', 'types', 're', 'string', 'bdb', 'pdb'):
            # nearly all modules use all of these... more or less. They add nothing to
            # our diagram.
            return 0
        if module_name.startswith('encodings.'):
            return 0
        # if s == '__main__':
        #     return 0  # 1
        if self.toocommon(module_name, kind):
            # A module where we dont want to draw references _to_. Dot doesnt handle these
            # well, so it is probably best to not draw them at all.
            return 0
        return 1

    def toocommon(self, module_name, kind):
        """Return true if references to this module are uninteresting. Such
           references do not get drawn. This is a default policy - please override.
        """
        if module_name == '__main__':
            # references *to* __main__ are never interesting. omitting them means
            # that main floats to the top of the page
            return 0
        if kind == imp.PKG_DIRECTORY:
            # dont draw references to packages.
            return 1
        return 0


def dep2dot(depgraph, color=True):
    dotter = PyDepGraphDot(colored=color)
    ctx = RenderContext()
    return dotter.render(depgraph, ctx)


def depgraph2dot():
    opts, args = getopt.getopt(sys.argv[1:], '-f:', ['mono', 'file='])

    _colored = True
    _output = sys.stdout
    for _opt, _val in opts:
        if _opt == '--mono':
            _colored = False
        if _opt in ('-f', '--file'):
            _output = open(_val, 'w')

    dotter = PyDepGraphDot(colored=_colored)
    ctx = RenderContext(_output)
    dotter.render(
        data=json.loads(sys.stdin.read()),
        ctx=ctx
    )
    _output.close()


if __name__ == '__main__':
    depgraph2dot()
