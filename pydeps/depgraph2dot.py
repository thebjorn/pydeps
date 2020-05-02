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
from .render_context import RenderBuffer
from . import colors


class PyDepGraphDot(object):
    def __init__(self, **kw):
        self.kw = kw

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
                )

            for a, b in sorted(depgraph):
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
            for src in sorted(visited):
                bg, fg = depgraph.get_colors(src, space)
                kwargs = {}

                if src.name in depgraph.cyclenodes:
                    kwargs['shape'] = 'octagon'

                ctx.write_node(
                    src.name,
                    label=src.get_label(splitlength=14,
                                        rmprefix=self.kw.get('rmprefix')),
                    fillcolor=colors.rgb2css(bg),
                    fontcolor=colors.rgb2css(fg),
                    **kwargs
                )

        return ctx.text()


class CycleGraphDot(object):
    def __init__(self, **kw):
        self.kw = kw

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
                )
                visited.add(a)
                visited.add(b)

            space = colors.ColorSpace(visited)
            for src in visited:
                bg, fg = depgraph.get_colors(src, space)
                kwargs = {}

                if src.name in depgraph.cyclenodes:
                    kwargs['shape'] = 'octagon'

                ctx.write_node(
                    src.name, label=src.label,
                    fillcolor=colors.rgb2css(bg),
                    fontcolor=colors.rgb2css(fg),
                    **kwargs
                )

        return ctx.text()


def dep2dot(target, depgraph, **kw):
    dotter = PyDepGraphDot(**kw)
    ctx = RenderBuffer(target, **kw)
    return dotter.render(depgraph, ctx)


def cycles2dot(target, depgraph, **kw):
    dotter = CycleGraphDot(**kw)
    ctx = RenderBuffer(target, **kw)
    return dotter.render(depgraph, ctx)
