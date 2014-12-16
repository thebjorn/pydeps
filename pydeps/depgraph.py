# -*- coding: utf-8 -*-
import json
import pprint
import enum
# from . import colors
import colors


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
    def __init__(self, name, kind=imp.UNKNOWN, path=None, imports=(), args=None):
        self.args = args or {}
        if name == "__main__" and path:
            self.name = path.replace('\\', '/').replace('/', '.')
            if self.args.get('verbose', 0) >= 2:
                print "changing __main__ =>", self.name
        else:
            self.name = name
        self.path = path            # needed here..?
        self.kind = kind
        self.imports = set(imports) # modules we import
        self.imported_by = set()    # modules that import us

    def __json__(self):
        res = dict(
            name=self.name,
            path=self.path,
            kind=str(self.kind)
        )
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
        return pprint.pformat(self.__dict__)

    def __iadd__(self, other):
        assert self.name == other.name
        self.path = self.path or other.path
        self.kind = self.kind or other.kind
        self.imports |= other.imports
        self.imported_by |= other.imported_by
        return self

    def imported_modules(self, depgraph):
        for name in self.imports:
            yield depgraph[name]

    @property
    def label(self):
        """Convert a module name to a formatted node label. This is a default
           policy - please override.
        """
        if len(self.name) > 14 and '.' in self.name:
            return '\\.\\n'.join(self.name.split('.'))
        return self.name

    @property
    def fillcolor(self):
        """Return the node color for this module name. This is a default
           policy - please override.

           Calculate a color systematically based on the hash of the module
           name. Modules in the same package have the same color. Unpackaged
           modules are grey
        """
        return self.colors()['bg']

    @property
    def fontcolor(self):
        return self.colors()['fg']

    def colors(self):
        bg = colors.name2rgb(self._color_base)
        fg = colors.foreground(bg, (255, 255, 255), (0, 0, 0))
        return dict(bg=colors.rgb2css(*bg), fg=colors.rgb2css(*fg))

    @property
    def _color_base(self):
        if self.kind == imp.PKG_DIRECTORY:
            return self.name
        else:
            i = self.name.rfind('.')
            if i < 0:
                return ''
            else:
                return self.name[:i]

    def weight(self, other):
        """Return the weight of the dependency from a to b. Higher weights
           usually have shorter straighter edges. Return 1 if it has normal
           weight. A value of 4 is usually good for ensuring that a related
           pair of modules are drawn next to each other. This is a default
           policy - please override.
        """
        if '_' + self.name == other.name:
            return 6

        if other.name.split('.')[-1].startswith('_'):
            # A module that starts with an underscore. You need a special reason to
            # import these (for example random imports _random), so draw them close
            # together
            return 4
        return 1

    def alien(self, other):
        """Return non-zero if references to this module are strange, and
            should be drawn extra-long. the value defines the length, in
            rank. This is also good for putting some vertical space between
            seperate subsystems. This is a default policy - please override.
         """
        return 0


class DepGraph(object):
    skip_modules = """
        os sys qt time __future__ types re string bdb pdb __main__
        south
        """.split()

    def __init__(self, depgraf, types, **args):
        self.args = args
        self.sources = {}             # module_name -> Source
        for name, imports in depgraf.items():
            self.verbose(4, "depgraph:", name, imports)
            src = Source(
                name=name,
                kind=imp(types.get(name, 0)),
                imports=imports.keys(),
                args=args
            )
            self.add_source(src)
            for iname, path in imports.items():
                src = Source(
                    name=iname,
                    kind=imp(types.get(name, 0)),
                    path=path,
                    args=args
                )
                self.add_source(src)
        self.verbose(1, "there are", len(self.sources), "modules")
        self.connect_generations()
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
        visited = set(self.skip_modules)

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

    def connect_generations(self):
        "Traverse depth-first adding imported_by."
        for src in self.sources.values():
            for _child in src.imports:
                child = self.sources[_child]
                child.imported_by.add(src.name)
