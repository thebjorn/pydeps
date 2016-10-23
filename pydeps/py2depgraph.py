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
import json
import os
import pprint
import sys
from collections import defaultdict

import enum
import yaml
from .pystdlib import pystdlib

from . import depgraph
from . import mf27
import logging
log = logging.getLogger(__name__)

PYLIB_PATH = depgraph.PYLIB_PATH


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


class Module(object):
    def __init__(self, name, file=None, path=None):
        self.__name__ = name
        self.__file__ = file
        self.__path__ = path
        self.__code__ = None
        # The set of global names that are assigned to in the module.
        # This includes those names imported through starimports of
        # Python modules.
        self.globalnames = {}
        # The set of starimports this module did that could not be
        # resolved, ie. a starimport from a non-Python module.
        self.starimports = {}

    @property
    def shortname(self):
        if self.__name__ == "__main__":
            return self.__file__[:-3].replace('\\', '.')
        return self.__name__

    def __repr__(self):
        return "Module(name=%s, file=%r, path=%r)" % (
            self.__name__,
            (self.__file__ or "").replace('\\', '/'),
            self.__path__
        )


class MyModuleFinder(mf27.ModuleFinder):
    def __init__(self, fname, *args, **kwargs):
        self.args = kwargs
        self.verbose = kwargs.get('verbose', 0)

        # include all of python std lib (incl. C modules)
        self.include_pylib_all = kwargs.pop('pylib_all', False)

        # include python std lib modules.
        # self.include_pylib = kwargs.pop('pylib', self.include_pylib_all)
        self.include_pylib = kwargs.pop('pylib', self.include_pylib_all)

        self._depgraph = defaultdict(dict)
        self._types = {}
        self._last_caller = None
        # path=None, debug=0, excludes=[], replace_paths=[]

        debug = 5 if self.verbose >= 4 else 0
        mf27.ModuleFinder.__init__(self,
                                   path=fname,
                                   debug=debug,
                                   excludes=kwargs.get('excludes', []))

    def add_module(self, fqname):
        if fqname in self.modules:
            return self.modules[fqname]
        self.modules[fqname] = m = Module(fqname)
        return m

    def import_hook(self, name, caller=None, fromlist=None, level=-1):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            # print "      last_CALLER:", caller, "OLD-lastcaller:", old_last_caller
            return mf27.ModuleFinder.import_hook(self, name, caller, fromlist, level)
        finally:
            self._last_caller = old_last_caller

    def _add_import(self, module):
        if module is not None:
            if self._last_caller:
                # self._depgraph[self._last_caller.__name__][module.__name__] = module.__file__
                if module.__file__ or self.include_pylib_all:
                    pylib_p = []
                    if not module.__file__:
                        pass
                    else:
                        rpath = os.path.split(module.__file__)[0].lower()
                        if 'site-packages' not in rpath:
                            pylib_p = [rpath.startswith(pp) for pp in PYLIB_PATH]
                    if self.include_pylib or not any(pylib_p):
                        # if self._last_caller.__name__ != module.__name__:
                        #     self._depgraph[self._last_caller.__name__][module.__name__] = module.__file__
                        self._depgraph[self._last_caller.__name__][module.__name__] = module.__file__

    def import_module(self, partnam, fqname, parent):
        module = mf27.ModuleFinder.import_module(self, partnam, fqname, parent)
        self._add_import(module)
        return module
    
    def load_module(self, fqname, fp, pathname, (suffix, mode, kind)):
        try:
            module = mf27.ModuleFinder.load_module(
                self, fqname, fp, pathname, (suffix, mode, kind)
            )
        except SyntaxError:
            # this happened first when pyinvoke tried to load yaml3/2 based on
            # an `if six.PY3`
            module = None
            
        if module is not None:
            self._types[module.__name__] = kind
        return module

    def ensure_fromlist(self, module, fromlist, recursive=0):
        self.msg(4, "ensure_fromlist", module, fromlist, recursive)
        for sub in fromlist:
            # print "  for sub:", sub, "in fromlisst:", fromlist, "hasattr(module, sub):", hasattr(module, sub)
            if sub == "*":
                # print "STAR"
                if not recursive:
                    submodules = self.find_all_submodules(module)
                    if submodules:
                        self.ensure_fromlist(module, submodules, 1)
            elif not hasattr(module, sub):
                # print "ELIF......"
                subname = "%s.%s" % (module.__name__, sub)
                submod = self.import_module(sub, subname, module)
                if not submod:
                    raise ImportError("No module named " + subname)
            else:
                self._add_import(getattr(module, sub))
                # print "  SUB:", sub, "lastcaller:", self._last_caller


class RawDependencies(object):
    def __init__(self, fname, **kw):
        path = sys.path[:]
        exclude = []
        mf = MyModuleFinder(path, exclude, **kw)
        mf.run_script(fname)
        self.depgraph = mf._depgraph
        self.types = mf._types


def pysource(fname):
    return not fname.startswith('.') and fname.endswith('.py')


def fname2modname(fname, package, prefix=""):
    pkg_dir, pkg_name = os.path.split(package)
    if fname.endswith('__init__.py'):
        return pkg_name

    if fname.startswith(package):
        fname = fname[len(pkg_dir) + 1: -3]
    return prefix + fname.replace('\\', '.').replace('/', '.')


def _pyfiles(directory, package=True, **args):
    for root, dirs, files in os.walk(directory):
        if package and '__init__.py' not in files:
            continue
        dotdirs = [d for d in dirs if d.startswith('.')]
        for d in dotdirs:
            dirs.remove(d)
        for fname in files:
            if pysource(fname):  # and fname not in args['exclude']:
                yield os.path.abspath(os.path.join(root, fname))


def is_module(directory):
    return os.path.isdir(directory) and '__init__.py' in os.listdir(directory)


def _create_dummy_module(package_name, **args):
    """Create a module that imports all files inside the package
    """
    dummy = '_dummy.py'
    package = os.path.abspath(package_name)

    prefix = []
    base, mod = os.path.split(package)
    while 1:
        if not is_module(base):
            break
        base, mod = os.path.split(base)
        prefix.insert(0, mod)
    prefix = '.'.join(prefix)
    if prefix:
        prefix += '.'

    def legal_module_name(name):
        for part in name.split('.'):
            try:
                exec "%s = 42" % part in {}, {}
            except:
                return False
        return True

    def print_import(fp, module):
        if 'migrations' in module:
            return
        if not legal_module_name(module):
            return
        print >>fp, "try:"
        print >>fp, "    import", module
        print >>fp, "except:"
        print >>fp, "    pass"

    if is_module(package):
        if args['verbose']: print "found package"
        with open(dummy, 'w') as fp:
            for fname in _pyfiles(package, **args):
                modname = fname2modname(fname, package, prefix)
                print_import(fp, modname)

    elif os.path.isdir(package):
        if args['verbose']: print "found directory"
        dummy = os.path.join(package, dummy)
        with open(dummy, 'w') as fp:
            for fname in os.listdir(package):
                if pysource(fname):
                    print_import(fp, fname2modname(fname, package))

    else:
        if args['verbose']: print "found file"
        # This return was an attempt at being able to analyze standalone
        # filenames with dashes (foo-bar.py). It does not work.
        # return package_name
        with open(dummy, 'w') as fp:
            print >>fp, "import", package_name

    return dummy


def _find_files(start, **args):
    if os.path.isdir(start):
        filenames = os.listdir(start)
        if '__init__.py' in filenames:
            if args['verbose'] >= 1: print 'found package:', start
            yield _create_dummy_module(start)
        else:
            for fname in filenames:
                yield fname
    else:
        yield start


def py2dep(pattern, **kw):
    fname = _create_dummy_module(pattern, **kw)
    path = sys.path[:]
    path.insert(0, os.path.dirname(fname))

    # remove exclude so we don't pass it twice to modulefinder
    exclude = ['migrations'] + kw.pop('exclude', [])
    log.debug("Exclude: %r", exclude)
    log.debug("KW: %r", kw)
    mf = MyModuleFinder(path, exclude, **kw)
    mf.run_script(fname)
    log.debug("mf._depgraph:\n%s", json.dumps(dict(mf._depgraph), indent=4))

    # remove dummy file and restore exclude argument
    os.unlink(fname)
    kw['exclude'] = exclude

    if kw.get('pylib'):
        mf_depgraph = mf._depgraph
        for k, v in mf._depgraph.items():
            log.debug('depgraph item: %r %r', k, v)
        # mf_modules = {k: os.path.abspath(v.__file__)
        #               for k, v in mf.modules.items()}
    else:
        pylib = pystdlib()
        mf_depgraph = {}
        for k, v in mf._depgraph.items():
            log.debug('depgraph item: %r %r', k, v)
            if k in pylib:
                continue
            vals = {vk: vv for vk, vv in v.items() if vk not in pylib}
            mf_depgraph[k] = vals

        # mf_modules = {k: os.path.abspath(v.__file__)
        #               for k, v in mf.modules.items()
        #               if k not in pylib}

    log.debug("mf_depgraph:\n%s",
              yaml.dump(dict(mf_depgraph), default_flow_style=False))
    # log.error("mf._types:\n%s", yaml.dump(mf._types, default_flow_style=False))
    # log.debug("mf_modules:\n%s", yaml.dump(mf_modules, default_flow_style=False))

    return depgraph.DepGraph(mf_depgraph, mf._types, **kw)


def py2depgraph():
    import json

    _fname = sys.argv[1]
    _graph = RawDependencies(_fname)

    sys.stdout.write(
        json.dumps(_graph.__dict__, indent=4)
    )


if __name__ == '__main__':
    py2depgraph()
