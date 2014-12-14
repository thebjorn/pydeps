# -*- coding: utf-8 -*-
import pprint
import enum


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
    def __init__(self, name, kind=imp.UNKNOWN, path=None, imports=()):
        self.name = name
        self.path = path            # needed here..?
        self.kind = kind
        self.imports = set(imports) # modules we import
        self.imported_by = set()    # modules that import us

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __iadd__(self, other):
        assert self.name == other.name
        self.path = self.path or other.path
        self.kind = self.kind or other.kind
        self.imports |= other.imports
        self.imported_by |= other.imported_by
        return self


class DepGraph(object):
    def __init__(self, depgraf, types):
        self.sources = {}             # module_name -> Source
        for name, imports in depgraf.items():
            src = Source(
                name=name,
                kind=imp(types.get(name, 0)),
                imports=imports.keys()
            )
            self.add_source(src)
            for iname, path in imports.items():
                src = Source(
                    name=iname,
                    kind=imp(types.get(name, 0)),
                    path=path,
                )
                self.add_source(src)
        self.connect_generations()

    def add_source(self, src):
        if src.name in self.sources:
            self.sources[src.name] += src
        else:
            self.sources[src.name] = src

    def __repr__(self):
        return repr(self.sources)

    def connect_generations(self):
        "Traverse depth-first adding imported_by."
        for src in self.sources.values():
            for _child in src.imports:
                child = self.sources[_child]
                child.imported_by.add(src.name)
