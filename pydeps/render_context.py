# -*- coding: utf-8 -*-
from collections import defaultdict
from io import StringIO
from contextlib import contextmanager
import textwrap
import enum


def to_unicode(s):
    try:
        return unicode(s)
    except NameError:
        return s


class Rankdir(enum.Enum):
    BOTTOM_TOP = 'BT'
    TOP_BOTTOM = 'TB'
    LEFT_RIGHT = 'LR'
    RIGHT_LEFT = 'RL'

    def reverse(self):
        return Rankdir(self.value[::-1])


class RenderContext(object):
    def __init__(self, out=None, reverse=False, rankdir=Rankdir.TOP_BOTTOM):
        self.out = out
        self.fp = StringIO()
        self.fillcolor = '#ffffff'
        self.fontcolor = '#000000'
        self.name = None
        self.concentrate = None
        self.compound = None
        self.width = 0.75
        self.reverse = reverse
        self.rankdir = rankdir

    @contextmanager
    def graph(self, **kw):
        """Set up a graphviz graph context.
        """
        self.name = kw.get('name', 'G')
        self.fillcolor = kw.get('fillcolor', '#ffffff')
        self.fontcolor = kw.get('fontcolor', '#000000')
        if kw.get('concentrate', True):
            self.concentrate = 'concentrate = true;'
        else:
            self.concentrate = ''
        self.compound = 'compound = true;' if kw.get('compound') else ''
        self.dedent("""
            digraph {self.name} {{
                {self.concentrate}
                {self.compound}
                rankdir = {self.rankdir.value};
                node [style=filled,fillcolor="{self.fillcolor}",fontcolor="{self.fontcolor}",fontname=Helvetica,fontsize=10];

        """.format(self=self))
        yield
        self.writeln('}')

    def text(self):
        """Get value of output stream (StringIO).
        """
        if self.out:
            self.out.close()  # pragma: nocover
        return self.fp.getvalue()

    def write_rule(self, a, b, **attrs):
        """a -> b [a1=x,a2=y];
        """
        if self.reverse:
            a, b = b, a
        with self.rule():
            self.write('%s -> %s' % (self._nodename(a), self._nodename(b)))
            # remove default values from output
            self._delattr(attrs, 'weight', 1)
            self._delattr(attrs, 'minlen', 1)
            self._delattr(attrs, 'len', 1)
            self.write_attributes(attrs)

    def write_node(self, a, **attrs):
        """a [a1=x,a2=y];
        """
        with self.rule():
            nodename = self._nodename(a)
            self.write(nodename)
            # remove default values from output
            self._delattr(attrs, 'label', nodename)
            self._delattr(attrs, 'fillcolor', self.fillcolor)
            self._delattr(attrs, 'fontcolor', self.fontcolor)
            self._delattr(attrs, 'width', self.width)
            self.write_attributes(attrs)

    # -- end of external/public interface --

    def write(self, txt):
        """Write ``txt`` to file and output stream (StringIO).
        """
        self.fp.write(to_unicode(txt))
        if self.out:
            self.out.write(txt)  # pragma: nocover

    def writeln(self, txt):
        """Write ``txt`` and add newline.
        """
        self.write(txt + '\n')

    def dedent(self, txt):
        """Write ``txt`` dedented.
        """
        self.write(textwrap.dedent(txt))

    def write_attributes(self, attrs):
        """Write comma separated attribute values (if exists).
        """
        if attrs:
            self.write(
                ' [' + ','.join('%s="%s"' % kv for kv in sorted(attrs.items())) + ']'
            )
        else:  # pragma: nocover
            pass

    def _nodename(self, x):
        """Return a valid node name.
        """
        return x.replace('.', '_')

    def _delattr(self, attr, key, value):
        if attr.get(key) == value:
            del attr[key]

    @contextmanager
    def rule(self):
        """Write indented rule.
        """
        self.write('    ')
        yield
        self.writeln(';')


class RenderBuffer(object):
    def __init__(self, target,
                 reverse=False,
                 rankdir=Rankdir.TOP_BOTTOM,
                 cluster=False,
                 min_cluster_size=0,
                 max_cluster_size=1,
                 keep_target_cluster=False,
                 collapse_target_cluster=False, **kw):
        self.target = target
        self.nodes = []
        self.clusters = defaultdict(list)
        self.rules = {}
        self.reverse = reverse
        self.rankdir = Rankdir(rankdir)
        if self.reverse:
            self.rankdir = self.rankdir.reverse()
        self.cluster = cluster
        self.min_cluster_size = min_cluster_size
        self.max_cluster_size = max_cluster_size
        self.graph_attrs = {}
        self.keep_target_cluster = keep_target_cluster
        self.collapse_target_cluster = collapse_target_cluster

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
        target_cluster = self._target_clusterid()

        _remove = []
        for clusterid, nodes in sorted(self.clusters.items()):
            if clusterid == target_cluster:
                # Target cluster must always be there, don't remove it even if it's small. We can get here
                # when --collapse-target-cluster flag is used.
                continue
            if len(nodes) < self.min_cluster_size:
                # print("REMOVING:CLUSTER:", clusterid, nodes)
                self.nodes += nodes
                _remove.append(clusterid)
        for _r in _remove:
            del self.clusters[_r]

    def _collapse_cluster(self, clusterid, nodes):
        """Add a single cluster node (with a label listing contents?)
           and change all rules to reference this node instead.
        """
        first_node, first_attrs = nodes[0]
        first_attrs['shape'] = 'folder'
        first_attrs['label'] = clusterid
        self.nodes.append((clusterid, first_attrs))

        for node, attrs in nodes:   # for each node in this cluster
            # check all rules for in/out relations
            rules = list(self.rules.items())
            self.rules = {}
            for (a, b), rule_attrs in rules:
                # orig = (a, b)
                if a == node:
                    a = clusterid
                if b == node:
                    b = clusterid
                # if orig != (a, b):
                #     print("CHANGED[{}|{}]: {} TO {}".format(clusterid, node, orig, (a, b)))
                self.rules[(a, b)] = rule_attrs

        del self.clusters[clusterid]

    def triage_clusters(self):
        target_cluster = self._target_clusterid()

        if not self.collapse_target_cluster and not self.keep_target_cluster:
            # don't put nodes from the target into a cluster
            self.nodes += self.clusters[target_cluster]
            del self.clusters[target_cluster]

        self._remove_small_clusters()

        # collapse target cluster if requested
        if self.collapse_target_cluster:
            self._collapse_cluster(target_cluster, self.clusters[target_cluster])

        # collapse clusters that are too big
        for clusterid, nodes in sorted(self.clusters.items()):
            if len(nodes) > self.max_cluster_size and clusterid != target_cluster:
                self._collapse_cluster(clusterid, nodes)

    def text(self):
        ctx = RenderContext(reverse=self.reverse, rankdir=self.rankdir)
        if self.cluster:
            self.triage_clusters()
            if self.clusters:   # are there any clusters left after triage?
                self.graph_attrs['compound'] = True
                self.graph_attrs['concentrate'] = False

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

    def _target_clusterid(self):
        return self._clusterid(self.target.fname)
