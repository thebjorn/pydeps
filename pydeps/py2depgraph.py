"""
# Copyright 2004,2009 Toby Dickenson
# Changes 2014 (c) Bjorn Pettersen
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
"""
import os
import pprint
import sys
import modulefinder
import enum
from collections import defaultdict

# we're not interested in imports of std python packages.
import depgraph

PYLIB_PATH = {
    # in virtualenvs that see the system libs, these will be different.
    os.path.split(os.path.split(modulefinder.__file__)[0])[0].lower(),
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


class MyModuleFinder(modulefinder.ModuleFinder):
    def __init__(self, fname, *args, **kwargs):
        print "MyModuelFinder:", fname, args, kwargs
        self.verbose = kwargs.get('verbose', False)

        # include all of python std lib (incl. C modules)
        self.include_pylib_all = kwargs.pop('pylib_all', False)

        # include python std lib modules.
        self.include_pylib = kwargs.pop('pylib', self.include_pylib_all)

        self._depgraph = defaultdict(dict)
        self._types = {}
        self._last_caller = None
        # path=None, debug=0, excludes=[], replace_paths=[]
        modulefinder.ModuleFinder.__init__(self,
                                           fname,
                                           kwargs.pop('debug', self.verbose),
                                           *args, **kwargs)

    def import_hook(self, name, caller=None, fromlist=None, level=None):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            return modulefinder.ModuleFinder.import_hook(self, name, caller, fromlist)
        finally:
            self._last_caller = old_last_caller
            
    def import_module(self, partnam, fqname, parent):
        r = modulefinder.ModuleFinder.import_module(self, partnam, fqname, parent)
        if r is not None and self._last_caller is not None:
            if r.__file__ or self.include_pylib_all:
                pylib_p = []
                if not r.__file__:
                    pass
                else:
                    rpath = os.path.split(r.__file__)[0].lower()
                    pylib_p = [rpath.startswith(pp) for pp in PYLIB_PATH]
                if self.include_pylib or not any(pylib_p):
                    self._depgraph[self._last_caller.__name__][r.__name__] = r.__file__
        return r
    
    def load_module(self, fqname, fp, pathname, (suffix, mode, type)):
        r = modulefinder.ModuleFinder.load_module(self, fqname, fp, pathname, (suffix, mode, type))
        if r is not None:
            self._types[r.__name__] = type
        return r


class RawDependencies(object):
    def __init__(self, fname, **kw):
        path = sys.path[:]
        exclude = []
        mf = MyModuleFinder(path, exclude, **kw)
        mf.run_script(fname)
        self.depgraph = mf._depgraph
        self.types = mf._types


def py2dep(fname, **kw):
    # path = sys.path[:]
    # exclude = []
    # mf = MyModuleFinder(path, exclude, **kw)
    # mf.run_script(fname)
    # return depgraph.DepGraph(mf._depgraph, mf._types)
    rawdeps = RawDependencies(fname, **kw)
    d = rawdeps.__dict__
    d['depgraph'] = dict(rawdeps.depgraph.items())
    return d


def py2depgraph():
    import json

    _fname = sys.argv[1]
    _graph = RawDependencies(_fname)

    sys.stdout.write(
        json.dumps(_graph.__dict__, indent=4)
    )

    # for node in depgraph.DepGraph(_graph).nodes.values():
    #     print 'node-name:', node.name
        # if node.name == 'datakortet.tt3.tt3page':
        #     print node
        #     print
        #     print node.name
        #     print 'imports:',
        #     pprint.pprint(node.imports)
        #     print 'imported_by:',
        #     pprint.pprint(node.imported_by)


if __name__ == '__main__':
    py2depgraph()
