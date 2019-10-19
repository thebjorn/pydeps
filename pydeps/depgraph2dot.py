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
from collections import defaultdict
from contextlib import contextmanager

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
            for src in visited:
                bg, fg = depgraph.get_colors(src, space)
                kwargs = {}

                if src.name in depgraph.cyclenodes:
                    kwargs['shape'] = 'octacon'

                ctx.write_node(
                    src.name, label=src.label,
                    fillcolor=colors.rgb2css(bg),
                    fontcolor=colors.rgb2css(fg),
                    **kwargs
                )

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
                )
                visited.add(a)
                visited.add(b)

            space = colors.ColorSpace(visited)
            for src in visited:
                bg, fg = depgraph.get_colors(src, space)
                kwargs = {}

                if src.name in depgraph.cyclenodes:
                    kwargs['shape'] = 'octacon'

                ctx.write_node(
                    src.name, label=src.label,
                    fillcolor=colors.rgb2css(bg),
                    fontcolor=colors.rgb2css(fg),
                    **kwargs
                )

        return ctx.text()


class RenderBuffer(object):
    def __init__(self, target, reverse=False, cluster_size=0):
        self.target = target
        self.nodes = []
        self.clusters = defaultdict(list)
        self.rules = []
        self.reverse = reverse
        self.cluster = cluster_size > 0
        self.min_cluster_size = cluster_size
        self.max_cluster_size = 5
        self.graph_attrs = {}

    def cluster_stats(self):
        maxnodes = max(len(v) for v in self.clusters.values())
        minnodes = min(len(v) for v in self.clusters.values())
        return minnodes, maxnodes

    def format_clusters(self):
        target_cluster = self._clusterid(self.target.fname)

        clusters = set()

        for clusterid, nodes in sorted(self.clusters.items()):
            if len(nodes) < self.min_cluster_size or clusterid == target_cluster:
                self.nodes += nodes
                continue

            if len(nodes) > self.max_cluster_size:
                continue

            clusters.add(clusterid)

        intercluster = set()
        for a, b, attrs in self.rules:
            cida = self._clusterid(a)
            cidb = self._clusterid(b)
            if cida == cidb:
                ctx.write_rule(a, b, **attrs)
            elif cida in clusters and cidb in clusters:
                if (cida, cidb) not in intercluster:
                    intercluster.add((cida, cidb))
                    attrs['ltail'] = 'cluster_' + cida
                    attrs['lhead'] = 'cluster_' + cidb
                    ctx.write_rule(a, b, **attrs)
            else:
                if cida in clusters:
                    attrs['ltail'] = 'cluster_' + cida
                if cidb in clusters:
                    attrs['lhead'] = 'cluster_' + cidb
                ctx.write_rule(a, b, **attrs)

    def text(self):
        ctx = RenderContext(reverse=self.reverse)
        if self.cluster:
            self.graph_attrs['compound'] = True
            self.graph_attrs['concentrate'] = False

            target_cluster = self._clusterid(self.target.fname)
            self.nodes += self.clusters[target_cluster]
            del self.clusters[target_cluster]

            # self.format_clusters()

        with ctx.graph(**self.graph_attrs):
            clusters = set()
            for clusterid, nodes in sorted(self.clusters.items()):
                if len(nodes) < self.min_cluster_size:
                    self.nodes += nodes
                    continue

                # if len(nodes) > self.max_cluster_size:
                #     continue

                clusters.add(clusterid)
                ctx.writeln('subgraph cluster_%s {' % clusterid)
                ctx.writeln('    label = %s;' % clusterid)
                for n, attrs in nodes:
                    ctx.write_node(n, **attrs)
                ctx.writeln('}')

            # non-clustered nodes
            for n, attrs in self.nodes:
                ctx.write_node(n, **attrs)

            intercluster = set()
            for a, b, attrs in self.rules:
                cida = self._clusterid(a)
                cidb = self._clusterid(b)
                if cida == cidb:
                    ctx.write_rule(a, b, **attrs)
                elif cida in clusters and cidb in clusters:
                    if (cida, cidb) not in intercluster:
                        intercluster.add((cida, cidb))
                        attrs['ltail'] = 'cluster_' + cida
                        attrs['lhead'] = 'cluster_' + cidb
                        ctx.write_rule(a, b, **attrs)
                else:
                    if cida in clusters:
                        attrs['ltail'] = 'cluster_' + cida
                    if cidb in clusters:
                        attrs['lhead'] = 'cluster_' + cidb
                    ctx.write_rule(a, b, **attrs)
        return ctx.text()

    @contextmanager
    def graph(self, **kw):
        self.graph_attrs.update(kw)
        yield

    def _clusterid(self, n):
        return n.split('.')[0].replace('_', '')

    def write_node(self, n, **attrs):
        clusterid = self._clusterid(n)
        if self.cluster:
            self.clusters[clusterid].append((n, attrs))
        else:
            self.nodes.append((n, attrs))

    def write_rule(self, a, b, **attrs):
        self.rules.append((a, b, attrs))


def dep2dot(target, depgraph, color=True, reverse=False):
    dotter = PyDepGraphDot(colored=color)
    ctx = RenderBuffer(target, reverse=reverse, cluster_size=1)
    return dotter.render(depgraph, ctx)


def cycles2dot(target, depgraph, reverse=False):
    dotter = CycleGraphDot()
    ctx = RenderBuffer(target, reverse=reverse)
    return dotter.render(depgraph, ctx)
