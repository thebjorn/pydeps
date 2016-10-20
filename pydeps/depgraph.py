# -*- coding: utf-8 -*-
from collections import defaultdict
import fnmatch
from itertools import izip_longest
import json
import os
import pprint
import re
import enum
from . import colors
import sys

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
    def __init__(self, name, kind=imp.UNKNOWN, path=None, imports=(), exclude=False, args=None):
        self.args = args or {}
        if name == "__main__" and path:
            self.name = path.replace('\\', '/').replace('/', '.')
            if self.args.get('verbose', 0) >= 2:  # pragma: nocover
                print "changing __main__ =>", self.name
        else:
            self.name = name
        self.kind = kind
        self.path = path             # needed here..?
        self.imports = set(imports)  # modules we import
        self.imported_by = set()     # modules that import us
        self.bacon = sys.maxint      # bacon distance
        self.excluded = exclude

    @property
    def name_parts(self):
        return self.name.split('.')

    @property
    def path_parts(self):
        p = self.path or ""
        return p.replace('\\', '/').lower().split('/')

    @property
    def in_degree(self):
        "Number of incoming arrows."
        return len(self.imports)

    @property
    def out_degree(self):
        "Number of outgoing arrows."
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
            kind=str(self.kind),
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
        return "%s (%s, %s)" % (self.name, self.path, self.kind)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return json.dumps(self.__json__(), indent=4)

    def __iadd__(self, other):
        assert self.name == other.name
        self.path = self.path or other.path
        self.kind = self.kind or other.kind
        self.imports |= other.imports
        self.imported_by |= other.imported_by
        return self

    # def imported_modules(self, depgraph):
    #     for name in self.imports:
    #         yield depgraph[name]

    @property
    def label(self):
        """Convert a module name to a formatted node label. This is a default
           policy - please override.
        """
        if len(self.name) > 14 and '.' in self.name:
            return '\\.\\n'.join(self.name.split('.'))
        return self.name

    @property
    def basename(self):
        if self.kind == imp.PKG_DIRECTORY or self.path.endswith('__init__.py'):
            return self.name
        else:
            i = self.name.rfind('.')
            if i < 0:
                return ''
            else:
                return self.name[:i]


class DepGraph(object):
    skip_modules = """
        os sys qt time __future__ types re string bdb pdb __main__
        south
        """.split()

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
        return path in PYLIB_PATH

    def proximity_metric(self, a, b):
        """Return the weight of the dependency from a to b. Higher weights
           usually have shorter straighter edges. Return 1 if it has normal
           weight. A value of 4 is usually good for ensuring that a related
           pair of modules are drawn next to each other.

           Returns an int between 1 (unknown, default), and 4 (very related).
        """
        # if self._is_pylib(a) and self._is_pylib(b):
        #     return 1

        res = 1
        for ap, bp, n in zip(a.path_parts, b.path_parts, range(4)):
            res += ap == bp
            if n >= 3:
                break
        return res

    def dissimilarity_metric(self, a, b):
        """Return non-zero if references to this module are strange, and
           should be drawn extra-long. The value defines the length, in
           rank. This is also good for putting some vertical space between
           seperate subsystems.

           Returns an int between 1 (default) and 4 (highly unrelated).
        """
        if self._is_pylib(a) and self._is_pylib(b):
            return 1

        res = 4
        for an, bn, n in izip_longest(a.name_parts, b.name_parts, range(4)):
            res -= an == bn
            if n >= 3:
                break
        return res

    def _exclude(self, name):
        return any(skip.match(name) for skip in self.skiplist)

    def __init__(self, depgraf, types, **args):
        self.curhue = 150  # start with a green-ish color
        self.colors = {}
        self.cycles = []
        self.cyclenodes = set()
        self.cyclerelations = set()

        self.args = args
        self.sources = {}             # module_name -> Source
        self.skiplist = [re.compile(fnmatch.translate(arg)) for arg in args['exclude']]

        for name, imports in depgraf.items():
            self.verbose(4, "depgraph:", name, imports)
            src = Source(
                name=name,
                kind=imp(types.get(name, 0)),
                imports=imports.keys(),
                args=args,
                exclude=self._exclude(name),
            )
            self.add_source(src)
            for iname, path in imports.items():
                src = Source(
                    name=iname,
                    kind=imp(types.get(name, 0)),
                    path=path,
                    args=args,
                    exclude=self._exclude(iname)
                )
                self.add_source(src)

        self.module_count = len(self.sources)
        self.verbose(1, "there are", self.module_count, "total modules")

        self.connect_generations()
        if self.args['show_cycles']:
            self.find_import_cycles()
        self.calculate_bacon()
        if self.args['show_raw_deps']:
            print self

        self.exclude_noise()
        self.exclude_bacon(self.args['max_bacon'])

        excluded = [v for v in self.sources.values() if v.excluded]
        self.skip_count = len(excluded)
        self.verbose(1, "skipping", self.skip_count, "modules")
        for module in excluded:
            self.verbose(2, "  ", module.name)

        self.remove_excluded()

        if not self.args['show_deps']:
            self.verbose(3, self)

    def verbose(self, n, *args):
        if self.args['verbose'] >= n:
            print ' '.join(str(a) for a in args)

    def add_source(self, src):
        if src.name in self.sources:
            self.sources[src.name] += src
        else:
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

                if impmod.path and not impmod.path.endswith('__init__.py'):
                    yield impmod, src
                visit(impmod)

        for _src in self.sources.values():
            for source in visit(_src):
                self.verbose(4, "Yielding", source[0], source[1])
                yield source

    def __repr__(self):
        return json.dumps(self.sources, indent=4, sort_keys=True,
                          default=lambda obj: obj.__json__() if hasattr(obj, '__json__') else obj)

    def find_import_cycles(self):
        def traverse(node, path):
            if node.name in self.cyclenodes:
                return
            
            if node.name in path:
                # found cycle
                cycle = path[path.index(node.name):] + [node.name]
                self.cycles.append(cycle)
                for nodename in cycle:
                    self.cyclenodes.add(nodename)
                for i in range(len(cycle)-1):
                    self.cyclerelations.add(
                        (cycle[i], cycle[i+1])
                    )
                return

            for impmod in node.imports:
                traverse(self.sources[impmod], path + [node.name])
        
        for src in self.sources.values():
            traverse(src, [])

    def connect_generations(self):
        "Traverse depth-first adding imported_by."
        for src in self.sources.values():
            for _child in src.imports:
                if _child in self.sources:
                    child = self.sources[_child]
                    child.imported_by.add(src.name)

    def calculate_bacon(self):
        count = defaultdict(int)

        def bacon(src, n):
            count[src.name] += 1
            # print 'bacon:', src, src.bacon, n,
            if src.bacon <= n:
                # print 'returning'
                return
            src.bacon = min(src.bacon, n)
            # print 'new bacon', src.bacon
            for imp in src.imports:
                bacon(self.sources[imp], n + 1)

        bacon(self.sources['__main__'], 0)
        # ritems = [(v, k) for k, v in count.items()]
        # for i, (v, k) in enumerate(sorted(ritems, reverse=True)):
        #     print k.rjust(25), v

    def exclude_noise(self):
        for src in self.sources.values():
            if src.excluded:
                continue
            if src.is_noise():
                self.verbose(2, "excluding", src, "because it is noisy:", src.degree)
                src.excluded = True
                self._add_skip(src.name)

    def exclude_bacon(self, limit):
        "Exclude models that are more than `limit` hops away from __main__."
        for src in self.sources.values():
            if src.bacon > limit:
                src.excluded = True
                self._add_skip(src.name)

    def remove_excluded(self):
        "Remove all sources marked as excluded."
        sources = self.sources.values()
        for src in sources:
            if src.excluded:
                del self.sources[src.name]
            src.imports = [m for m in src.imports if not self._exclude(m)]
            src.imported_by = [m for m in src.imported_by if not self._exclude(m)]

    def _add_skip(self, name):
        self.skiplist.append(re.compile(fnmatch.translate(name)))
