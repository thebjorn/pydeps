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


class Source(object):
    def __init__(self, name, path=None):
        self.name = name
        self.path = path        # needed here..?
        self.type = 0
        self.imports = set()      # modules we import
        self.imported_by = set()  # modules that import us

    def __repr__(self):
        return pprint.pformat(self.__dict__)


class DepGraph(object):
    def __init__(self, rawdeps):
        self.nodes = {}
        self.insert_nodes(rawdeps)
        self.connect_generations()

    def __repr__(self):
        return repr(self.nodes)

    def insert_nodes(self, rawdeps):
        for rsrc in rawdeps.depgraph:
            src = self.nodes.get(rsrc) or Source(rsrc)
            if rsrc in rawdeps.types:
                src.type = imp(rawdeps.types[rsrc])
            src.imports |= set(rawdeps.depgraph[rsrc].keys())
            self.nodes[src.name] = src

    def connect_generations(self):
        for node in self.nodes.values():
            for _child in node.imports:
                if _child not in self.nodes:
                    continue
                child = self.nodes[_child]
                child.imported_by.add(node.name)
