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

from . import colors
from .render_context import RenderContext


class PyDepGraphDot(object):
    def __init__(self, colored=True):
        self.colored = colored

    def render(self, depgraph, ctx):
        with ctx.graph():
            visited = set()
            drawn = set()

            for aname, bname in depgraph.cyclerelations:
                try:
                    a = depgraph.sources[aname]
                    b = depgraph.sources[bname]
                except KeyError:
                    continue
                drawn.add((bname, aname))
                ctx.write_rule(
                    aname, bname,
                    weight=depgraph.proximity_metric(a, b),
                    minlen=depgraph.dissimilarity_metric(a, b),
                    #style='dotted',
                )

            for a, b in depgraph:
                # b imports a
                aname = a.name
                bname = b.name
                if (bname, aname) in drawn:
                    continue
                drawn.add((bname, aname))

                ctx.write_rule(
                    aname, bname,
                    weight=depgraph.proximity_metric(a, b),
                    minlen=depgraph.dissimilarity_metric(a, b))

                visited.add(a)
                visited.add(b)

            space = colors.ColorSpace(visited)
            # print space

            for src in visited:
                bg, fg = depgraph.get_colors(src, space)
                if src.name in depgraph.cyclenodes:
                    ctx.write_node(src.name, label=src.label,
                                   fillcolor=colors.rgb2css(bg),
                                   fontcolor=colors.rgb2css(fg),
                                   shape='octagon')
                else:
                    ctx.write_node(src.name, label=src.label,
                                   fillcolor=colors.rgb2css(bg),
                                   fontcolor=colors.rgb2css(fg))

        return ctx.text()


class CycleGraphDot(object):
    def __init__(self, colored=True):
        self.colored = colored

    def render(self, depgraph, ctx):
        with ctx.graph(concentrate=False):
            visited = set()
            drawn = set()

            for aname, bname in depgraph.cyclerelations:
                try:
                    a = depgraph.sources[aname]
                    b = depgraph.sources[bname]
                except KeyError:
                    continue
                drawn.add((bname, aname))
                ctx.write_rule(
                    bname, aname,
                    weight=depgraph.proximity_metric(a, b),
                    minlen=depgraph.dissimilarity_metric(a, b),
                    # style='dotted',
                )
                visited.add(a)
                visited.add(b)

            space = colors.ColorSpace(visited)
            for src in visited:
                bg, fg = depgraph.get_colors(src, space)
                if src.name in depgraph.cyclenodes:
                    ctx.write_node(src.name, label=src.label,
                                   fillcolor=colors.rgb2css(bg),
                                   fontcolor=colors.rgb2css(fg),
                                   shape='octagon')
                else:
                    ctx.write_node(src.name, label=src.label,
                                   fillcolor=colors.rgb2css(bg),
                                   fontcolor=colors.rgb2css(fg))

        return ctx.text()


def dep2dot(depgraph, color=True):
    dotter = PyDepGraphDot(colored=color)
    ctx = RenderContext()
    return dotter.render(depgraph, ctx)


def cycles2dot(depgraph):
    dotter = CycleGraphDot()
    ctx = RenderContext()
    return dotter.render(depgraph, ctx)


# def depgraph2dot():  # pragma: nocover
#     opts, _args = getopt.getopt(sys.argv[1:], '-f:', ['mono', 'file='])

#     _colored = True
#     _output = sys.stdout
#     for _opt, _val in opts:
#         if _opt == '--mono':
#             _colored = False
#         if _opt in ('-f', '--file'):
#             _output = open(_val, 'w')

#     dotter = PyDepGraphDot(colored=_colored)
#     ctx = RenderContext(_output)
#     dotter.render(
#         data=json.loads(sys.stdin.read()),
#         ctx=ctx
#     )
#     _output.close()


# if __name__ == '__main__':  # pragma: nocover
#     depgraph2dot()
