# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import defaultdict, deque
import fnmatch
from .pycompat import zip_longest
import json
import os
import pprint
import re
import enum

from . import colors, cli
import sys
import logging
log = logging.getLogger(__name__)

# we're normally not interested in imports of std python packages.
PYLIB_PATH = {
    # in virtualenvs that see the system libs, these will be different.
    os.path.split(os.path.split(pprint.__file__)[0])[0].lower(),
    os.path.split(os.__file__)[0].lower()
}


class imp(enum.Enum):
    C_BUILTIN = 6
    C_EXTENSION = 3
    IMP_HOOK = 9
    PKG_DIRECTORY = 5
    PY_CODERESOURCE = 8
    PY_COMPILED = 2
    PY_FROZEN = 7
    PY_RESOURCE = 4
    PY_SOURCE = 1
    UNKNOWN = 0


class Source(object):
    """A node (contained) in the dependency graph.

       It contains info about which modules are imported by this source,
       and which modules import this source.
    """
    def __init__(self, name, path=None, imports=(), exclude=False, args=None):
        self.args = args or {}
        self.name = name
        # self.kind = kind
        self.path = path             # needed here..?
        self.imports = set(imports)  # modules we import
        self.imported_by = set()     # modules that import us
        self.bacon = sys.maxsize      # bacon distance
        self.excluded = exclude

    @property
    def name_parts(self):
        return self.name.split('.')

    @property
    def module_depth(self):
        return self.name.count('.')

    @property
    def path_parts(self):
        p = self.path or ""
        return p.replace('\\', '/').lower().split('/')

    @property
    def in_degree(self):
        """Number of incoming arrows.
        """
        return len(self.imports)

    @property
    def out_degree(self):
        """Number of outgoing arrows.
        """
        return len(self.imported_by)

    @property
    def degree(self):
        return self.in_degree + self.out_degree

    def is_noise(self):
        """Is this module just noise?  (too common either at top or bottom of
           the graph).
        """
        noise = self.args['noise_level']
        if not (self.in_degree and self.out_degree):
            return self.degree > noise
        return False

    def __json__(self):
        res = dict(
            name=self.name,
            path=self.path,
            # kind=str(self.kind),
            bacon=self.bacon,
        )
        if self.excluded:
            res['excluded'] = 'EXCLUDED'
        if self.imports:
            res['imports'] = list(sorted(self.imports))
        if self.imported_by:
            res['imported_by'] = list(sorted(self.imported_by))
        return res

    def __str__(self):
        return "%s (%s)" % (self.name, self.path)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __le__(self, other):
        return self.name <= other.name

    def __gt__(self, other):
        return self.name > other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __repr__(self):
        return json.dumps(self.__json__(), indent=4)

    def __iadd__(self, other):
        """Merge other into self.
        """
        if self.name == other.name and self.imports == other.imports and self.bacon == other.bacon:
            return self
        log.debug("iadd lhs: %r", self)
        log.debug("iadd rhs: %r", other)
        assert self.name == other.name
        self.path = self.path or other.path
        self.imports |= other.imports
        self.imported_by |= other.imported_by
        self.bacon = min(self.bacon, other.bacon)
        self.excluded = self.excluded or other.excluded
        log.debug("iadd result: %r", self)
        return self

    def get_label(self, splitlength=0, rmprefix=None):
        name = self.name
        if rmprefix:
            for prefix in rmprefix:
                if self.name.startswith(prefix):
                    name = self.name[len(prefix):]
                    break
        if splitlength and len(name) > splitlength and '.' in name:
            return '\\.\\n'.join(name.split('.'))  # pragma: nocover
        return name

    @property
    def label(self):
        """Convert a module name to a formatted node label. This is a default
           policy - please override.
        """
        return self.get_label(splitlength=14)


class GraphNode:
    def __init__(self, src, index=None):
        self.src = src
        self.index = index
        # self.inlinks = []
        # self.outlinks = []

    def __str__(self):
        return self.src.name
    
    def __repr__(self):
        return self.src.name

    def __hash__(self):
        return hash(self.src.name)

    def __eq__(self, other):
        return self.src.name == other.src.name

    def __json__(self):
        return self.src.name


class GraphNodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, GraphNode):
            return obj.name
        return super().default(obj)


class Graph:
    def __init__(self, vertices: list[GraphNode], edges: list[tuple[GraphNode, GraphNode]]):
        self.V = vertices
        for i, v in enumerate(vertices):
            v.index = i
        self.edges = edges
        self.neighbours = defaultdict(list)
        for u, v in edges:
            self.neighbours[u].append(v)

    def __json__(self):
        return {
            "edges": [(u, v) for u, v in self.edges],
            "neighbours": {u.__json__(): [v.__json__() for v in self.neighbours[u]] for u in self.V}
        }
    
    def __str__(self):
        return json.dumps(self, indent=4, cls=GraphNodeEncoder)

    def transpose(self):
        return Graph(self.V, [(v, u) for u, v in self.edges])

    def dfs(self, v, visited, stack):
        visited[v.index] = True
        for neighbour in self.neighbours[v]:
            if not visited[neighbour.index]:
                self.dfs(neighbour, visited, stack)
        stack.append(v)
 
    
    def fill_order(self):
        def _fill_order(visited, stack):
            for i, node in enumerate(self.V):
                if not visited[i]:
                    self.dfs(node, visited, stack)
        visited = [False] * len(self.V)
        stack = deque()
        _fill_order(visited, stack)
        return stack

    def dfs_util(self, v, visited):
        component = []

        def _dfs_util(v, visited):
            visited[v.index] = True
            component.append(v)
            for neighbour in self.neighbours[v]:
                if not visited[neighbour.index]:
                    _dfs_util(neighbour, visited)

        _dfs_util(v, visited)
        return set(component)

    def kosaraju(self):
        stack = self.fill_order()
        transposed_graph = self.transpose()
        
        visited = [False] * len(self.V)
        scc_list = []
        
        while stack:
            node = stack.pop()  # popleft?
            if not visited[node.index]:
                component = transposed_graph.dfs_util(node, visited)
                scc_list.append(component)
        return sorted(scc_list, key=lambda x: len(x), reverse=True)


class DepGraph(object):
    """The dependency graph.

       It is the output of :func:`pydeps.py2depgraph.py2dep`
    """
    skip_modules = """
        os sys qt time __future__ types re string bdb pdb __main__
        south
        """.split()

    def __init__(self, depgraf, types, target, **args):
        # depgraph is py2depgraph.MyModulefinder._depgraph
        log.debug("DepGraph: depgraf=%r", depgraf)

        self.curhue = 150  # start with a green-ish color
        self.colors = {}

        self.cycles = []
        self.cyclenodes = set()
        self.cyclerelations = set()
        
        self.max_module_depth = args.get('max_module_depth', 0)
        self.target = target

        self.args = args

        #: dict[module_name] -> Source object
        self.sources = {}
        self.skiplist = [re.compile(fnmatch.translate(arg)) for arg in args['exclude']]
        self.skiplist += [re.compile('^%s$' % fnmatch.translate(arg)) for arg in args['exclude_exact']]
        # depgraf = {name: imports for (name, imports) in depgraf.items()}

        for name, imports in depgraf.items():
            log.debug("depgraph name=%r imports=%r", name, imports)
            src = Source(
                name=self.source_name(name),
                imports=[self.source_name(n) for n in imports.keys()],  # values handled below
                args=args,
                exclude=self._exclude(name),
            )
            log.debug("depgraph src=%r", src)
            self.add_source(src)
            for iname, path in imports.items():
                src = Source(
                    name=self.source_name(iname, path),
                    path=path,
                    args=args,
                    exclude=self._exclude(iname)
                )
                self.add_source(src)

        self.module_count = len(self.sources)
        cli.verbose(1, "there are", self.module_count, "total modules")

        self.connect_generations()
        # if self.args['show_cycles']:
        #     self.find_import_cycles()
        self.calculate_bacon()
        if self.args['show_raw_deps']:
            print(self)

        self.exclude_noise()
        self.exclude_bacon(self.args['max_bacon'])
        self.only_filter(self.args.get('only'))

        excluded = [v for v in list(self.sources.values()) if v.excluded]
        # print "EXCLUDED:", excluded
        self.skip_count = len(excluded)
        cli.verbose(1, "skipping", self.skip_count, "modules")
        for module in excluded:
            # print 'exclude:', module.name
            cli.verbose(2, "  ", module.name)

        self.remove_excluded()

        # if self.args['show_cycles']:
        self.find_import_cycles()
        
        if not self.args['show_deps']:
            cli.verbose(3, self)

    def source_name(self, name, path=None):
        """Returns the module name, possibly limited by --max-module-depth.
        """
        res = name
        if name == "__main__" and self.target.is_pysource:
            # use the target file name directly if we're working on a 
            # single file
            return self.target.fname

        if name == "__main__" and path:
            # use the path to the main module if we're working on a module.
            res = path.replace('\\', '/').replace('/', '.')
            if self.args.get('verbose', 0) >= 2:  # pragma: nocover
                print("changing __main__ =>", res)

        if self.max_module_depth > 0:
            res = '.'.join(res.split('.')[:self.max_module_depth])
        return res

    def __json__(self):
        return json.dumps(self.sources, indent=4, sort_keys=True,
                          default=lambda obj: obj.__json__() if hasattr(obj, '__json__') else obj)

    def levelcounts(self):
        pass

    def get_colors(self, src, colorspace=None):
        if colorspace is None:
            if src.basename not in self.colors:
                h = self.curhue
                # self.curhue += 7  # relative prime with 360
                self.curhue += 37  # relative prime with 360
                self.curhue %= 360
                # print "NAME:", src.name, "BASENAME:", src.basename
                bg = colors.name2rgb(h)
                black = (0, 0, 0)
                white = (255, 255, 255)
                fg = colors.foreground(bg, black, white)
                self.colors[src.basename] = bg, fg
            return self.colors[src.basename]
        else:
            return colorspace.color(src)

    def _is_pylib(self, path):
        log.info('path %r in PYLIB_PATH %r => %s', path, PYLIB_PATH, path in PYLIB_PATH)
        return path in PYLIB_PATH

    def proximity_metric(self, a, b):
        """Return the weight of the dependency from a to b. Higher weights
           usually have shorter straighter edges. Return 1 if it has normal
           weight. A value of 4 is usually good for ensuring that a related
           pair of modules are drawn next to each other.

           Returns an int between 1 (unknown, default), and 4 (very related).
        """
        res = 0
        for ap, bp, n in zip(a.name_parts, b.name_parts, list(range(4))):
            res += ap == bp
            if n >= 3:
                break
        if res == 0: res = 1    # noqa
        return 4 if res > 4 else res

    def dissimilarity_metric(self, a, b):
        """Return non-zero if references to this module are strange, and
           should be drawn extra-long. The value defines the length, in
           rank. This is also good for putting some vertical space between
           seperate subsystems.

           Returns an int between 1 (default) and 4 (highly unrelated).
        """
        res = 4
        for an, bn, n in zip_longest(a.name_parts, b.name_parts, list(range(4))):
            res -= an == bn
            if n >= 3:
                break
        return 4 if res > 4 else res

    def _exclude(self, name):
        return any(skip.match(name) for skip in self.skiplist)

    def add_source(self, src):
        if src.name in self.sources:
            log.debug("ADD-SOURCE[+=]\n%r", src)
            self.sources[src.name] += src   # merge
        else:
            log.debug("ADD-SOURCE[=]\n%r", src)
            self.sources[src.name] = src

    def __getitem__(self, item):
        return self.sources[item]

    def __iter__(self):
        visited = set(self.skip_modules) | set(self.args['exclude'])

        def visit(src):
            if src.name in visited:
                return
            visited.add(src.name)
            for name in src.imports:
                impmod = self.sources[name]

                # FIXME: why do we want to exclude **/*/__init__.py? This line
                # causes `collections` package in py3 to be excluded.
                # if impmod.path and not impmod.path.endswith('__init__.py'):
                if not src.name.startswith(impmod.name + "."):
                    yield impmod, src
                visit(impmod)

        for _src in self.sources.values():
            for source in visit(_src):
                cli.verbose(4, "Yielding", source[0], source[1])
                yield source

    def __repr__(self):
        return json.dumps(self.sources, indent=4, sort_keys=True,
                          default=lambda obj: obj.__json__() if hasattr(obj, '__json__') else obj)

    def find_import_cycles(self):
        """Divide the graph into strongly connected components using kosaraju's algorithm.
        """

        vertices = {src.name: GraphNode(src) for src in sorted(
            self.sources.values(), key=lambda x: x.name.lower()
        )}
        edges = []
        for u in vertices.values():
            for v in u.src.imported_by:
                tmp = self.sources[v]
                edges.append((u, vertices[tmp.name]))
        graph = Graph(vertices.values(), edges)

        scc = [c for c in graph.kosaraju() if len(c) > 1]
        self.cycles = [[n.src for n in c] for c in scc]
        for c in scc:
            for node in c:
                self.cyclenodes.add(node.src.name)
            # c = list(c)
            # for i in range(len(c) - 1):
            #     self.cyclerelations.add((c[i].src.name, c[i + 1].src.name))

    def connect_generations(self):
        """Traverse depth-first adding imported_by.
        """
        for src in self.sources.values():
            for _child in src.imports:
                if _child in self.sources:
                    child = self.sources[_child]
                    child.imported_by.add(src.name)

    def calculate_bacon(self):
        count = defaultdict(int)

        def bacon(src, n):
            count[src.name] += 1
            if src.bacon <= n:
                return
            src.bacon = min(src.bacon, n)
            for imp in src.imports:
                bacon(self.sources[imp], n + 1)

        if '__main__' in self.sources:
            bacon(self.sources['__main__'], 0)
        elif self.args['dummyname'] in self.sources:
            bacon(self.sources[self.args['dummyname']], 0)

    def exclude_noise(self):
        for src in list(self.sources.values()):
            if src.excluded:
                continue
            if src.is_noise():
                cli.verbose(2, "excluding", src, "because it is noisy:", src.degree)
                src.excluded = True
                self._add_skip(src.name)

    def exclude_bacon(self, limit):
        """Exclude modules that are more than `limit` hops away from __main__.
        """
        for src in list(self.sources.values()):
            if src.bacon > limit:
                src.excluded = True
                self._add_skip(src.name)

    def only_filter(self, paths):
        """Exclude nodes that have a prefix in paths.
        """
        if not paths:
            return
        paths = set(paths)

        def should_include(node):
            for p in paths:
                if node.name.startswith(p):
                    return True
            return False

        for src in list(self.sources.values()):
            if not should_include(src):
                src.excluded = True
                # print "Excluding bacon:", src.name
                self._add_skip(src.name)

    def remove_excluded(self):
        """Remove all sources marked as excluded.
        """
        sources = list(self.sources.values())
        for src in sources:
            if src.excluded:
                del self.sources[src.name]
            src.imports = [m for m in src.imports if not self._exclude(m)]
            src.imported_by = [m for m in src.imported_by if not self._exclude(m)]

    def _add_skip(self, name):
        # print 'add skip:', name
        self.skiplist.append(re.compile(fnmatch.translate(name)))
