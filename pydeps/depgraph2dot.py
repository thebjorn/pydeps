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
    def __init__(self, target,
                 reverse=False,
                 cluster=False,
                 min_cluster_size=0,
                 max_cluster_size=1,
                 keep_target_cluster=False):
        self.target = target
        self.nodes = []
        self.clusters = defaultdict(list)
        self.rules = {}
        self.reverse = reverse
        self.cluster = cluster
        self.min_cluster_size = min_cluster_size
        self.max_cluster_size = max_cluster_size
        self.graph_attrs = {}
        self.keep_target_cluster = keep_target_cluster

    def _nodecolor(self, n):
        for node, attrs in self.nodes:
            if node == n:
                return attrs['fillcolor']
        return '#000000'

    def cluster_stats(self):
        maxnodes = max(len(v) for v in self.clusters.values())
        minnodes = min(len(v) for v in self.clusters.values())
        return minnodes, maxnodes

    def _remove_small_clusters(self):
        # remove clusters that are too small
        _remove = []
        for clusterid, nodes in sorted(self.clusters.items()):
            if len(nodes) < self.min_cluster_size:
                print("REMOVING:CLUSTER:", clusterid, nodes)
                self.nodes += nodes
                _remove.append(clusterid)
        for _r in _remove:
            del self.clusters[_r]

    def _collapse_cluster(self, clusterid, nodes):
        """Add a single cluster node (with a label listing contents?)
           and change all rules to reference this node instead.
        """
        first_node, first_attrs = nodes[0]
        # self.nodes.append((clusterid, first_attrs))

        tmp = nodes[:]
        nodes[:] = [(clusterid, first_attrs)]
        for node, attrs in tmp:
            rules = list(self.rules.items())
            self.rules = {}
            for (a, b), rule_attrs in rules:
                orig = (a, b)
                if a == node:
                    a = clusterid
                if b == node:
                    b = clusterid
                # if orig != (a, b):
                #     print("CHANGED[{}|{}]: {} TO {}".format(clusterid, node, orig, (a, b)))
                self.rules[(a, b)] = rule_attrs

    def triage_clusters(self):
        target_cluster = self._clusterid(self.target.fname)
        if not self.keep_target_cluster:
            # don't put nodes from the target into a cluster
            self.nodes += self.clusters[target_cluster]
            del self.clusters[target_cluster]

        self._remove_small_clusters()

        # collapse clusters that are too big
        for clusterid, nodes in sorted(self.clusters.items()):
            if len(nodes) > self.max_cluster_size and clusterid != target_cluster:
                self._collapse_cluster(clusterid, nodes)

    def text(self):
        for (a, b), attrs in sorted(self.rules.items()):
            if a.startswith('dkdj'):
                print '{} -> {}'.format(a, b)

        ctx = RenderContext(reverse=self.reverse)
        if self.cluster:
            self.graph_attrs['compound'] = True
            self.graph_attrs['concentrate'] = False
            self.triage_clusters()

        with ctx.graph(**self.graph_attrs):
            clusters = set()
            for clusterid, nodes in sorted(self.clusters.items()):
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
            for (a, b), attrs in sorted(self.rules.items()):
                if a == b:
                    continue
                cida = self._clusterid(a)
                cidb = self._clusterid(b)
                if cida == cidb:
                    if self.reverse:
                        attrs['fillcolor'] = self._nodecolor(b)
                    else:
                        attrs['fillcolor'] = self._nodecolor(a)
                    ctx.write_rule(a, b, **attrs)
                elif cida in clusters and cidb in clusters:
                    if (cida, cidb) not in intercluster:
                        intercluster.add((cida, cidb))
                        if self.reverse:
                            attrs['lhead'] = 'cluster_' + cida
                            attrs['ltail'] = 'cluster_' + cidb
                            attrs['fillcolor'] = self._nodecolor(b)
                        else:
                            attrs['ltail'] = 'cluster_' + cida
                            attrs['lhead'] = 'cluster_' + cidb
                            attrs['fillcolor'] = self._nodecolor(a)
                        ctx.write_rule(a, b, **attrs)
                else:
                    if cida in clusters:
                        if self.reverse:
                            attrs['lhead'] = 'cluster_' + cida
                        else:
                            attrs['ltail'] = 'cluster_' + cida
                    if cidb in clusters:
                        if self.reverse:
                            attrs['ltail'] = 'cluster_' + cidb
                        else:
                            attrs['lhead'] = 'cluster_' + cidb
                    if self.reverse:
                        attrs['fillcolor'] = self._nodecolor(b)
                    else:
                        attrs['fillcolor'] = self._nodecolor(a)
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
        self.rules[(a, b)] = attrs


def dep2dot(target, depgraph, color=True, reverse=False):
    dotter = PyDepGraphDot(colored=color)
    ctx = RenderBuffer(
        target, reverse=reverse,
        cluster=True,
        min_cluster_size=0,
        max_cluster_size=1,
        keep_target_cluster=True
    )
    return dotter.render(depgraph, ctx)


def cycles2dot(target, depgraph, reverse=False):
    dotter = CycleGraphDot()
    ctx = RenderBuffer(target, reverse=reverse)
    return dotter.render(depgraph, ctx)
