
# from .mf.mf_next import *     # for debugging next version
import modulefinder
from modulefinder import (
    ModuleFinder as NativeModuleFinder
)
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', PendingDeprecationWarning)
    import imp
import marshal
import dis

HAVE_ARGUMENT = dis.HAVE_ARGUMENT

# monkey-patch broken modulefinder._find_module 
# (https://github.com/python/cpython/issues/84530)
# in Python 3.8-3.10
if hasattr(modulefinder, '_find_module'):
    modulefinder._find_module = imp.find_module


class ModuleFinder(NativeModuleFinder):
    def import_hook(self, name, caller=None, fromlist=None, level=-1):
        self.msg(3, "import_hook: name(%s) caller(%s) fromlist(%s) level(%s)" % (name, caller, fromlist, level))
        parent = self.determine_parent(caller, level=level)
        q, tail = self.find_head_package(parent, name)
        if q.shortname in ('__future__', 'future'):  # [pydeps] the future package causes recursion overflow
            return None
        m = self.load_tail(q, tail)
        if not fromlist:
            return q
        if m.__path__:
            self.ensure_fromlist(m, fromlist)
        return None

    def load_module(self, fqname, fp, pathname, file_info):
        # fqname = dotted module name we're loading
        suffix, mode, kind = file_info
        kstr = {
            imp.PKG_DIRECTORY: 'PKG_DIRECTORY',
            imp.PY_SOURCE: 'PY_SOURCE',
            imp.PY_COMPILED: 'PY_COMPILED',
        }.get(kind, 'unknown-kind')
        self.msgin(2, "load_module(%s) fqname=%s, fp=%s, pathname=%s" % (kstr, fqname, fp and "fp", pathname))

        if kind == imp.PKG_DIRECTORY:
            module = self.load_package(fqname, pathname)
            self.msgout(2, "load_module ->", module)
            return module

        if kind == imp.PY_SOURCE:
            txt = fp.read()
            txt += b'\n' if isinstance(txt, bytes) else '\n'
            co = compile(
                txt,
                pathname,
                'exec',            # compile code block
                dont_inherit=True  # [pydeps] don't inherit future statements from current environment
            )

        elif kind == imp.PY_COMPILED:
            # a .pyc file is a binary file containing only thee things:
            #  1. a four-byte magic number
            #  2. a four byte modification timestamp, and
            #  3. a Marshalled code object
            # from: https://nedbatchelder.com/blog/200804/the_structure_of_pyc_files.html
            if fp.read(4) != imp.get_magic():
                self.msgout(2, "raise ImportError: Bad magic number", pathname)
                raise ImportError("Bad magic number in %s" % pathname)
            fp.read(4)   # skip modification timestamp
            co = marshal.load(fp)  # load marshalled code object.

        else:
            co = None
        m = self.add_module(fqname)
        m.__file__ = pathname
        if co:
            if self.replace_paths:
                co = self.replace_paths_in_code(co)
            m.__code__ = co
            self.scan_code(co, m)
        self.msgout(2, "load_module ->", m)
        return m

    def scan_code(self, co, m):
        code = co.co_code   # noqa
        # if sys.version_info >= (3, 4):
        #     scanner = self.scan_opcodes
        # elif sys.version_info >= (2, 5):
        #     scanner = self.scan_opcodes_25
        # else:
        #     scanner = self.scan_opcodes_24
        scanner = self.scan_opcodes
        for what, args in scanner(co):
            if what == "store":
                name, = args
                m.globalnames[name] = 1
            elif what in ("import", "absolute_import"):
                fromlist, name = args
                have_star = 0
                if fromlist is not None:
                    if "*" in fromlist:
                        have_star = 1
                    fromlist = [f for f in fromlist if f != "*"]
                if what == "absolute_import":
                    level = 0
                else:
                    level = -1
                self._safe_import_hook(name, m, fromlist, level=level)
                if have_star:
                    # We've encountered an "import *". If it is a Python module,
                    # the code has already been parsed and we can suck out the
                    # global names.
                    mm = None
                    if m.__path__:
                        # At this point we don't know whether 'name' is a
                        # submodule of 'm' or a global module. Let's just try
                        # the full name first.
                        mm = self.modules.get(m.__name__ + "." + name)
                    if mm is None:
                        mm = self.modules.get(name)
                    if mm is not None:
                        m.globalnames.update(mm.globalnames)
                        m.starimports.update(mm.starimports)
                        if mm.__code__ is None:
                            m.starimports[name] = 1
                    else:
                        m.starimports[name] = 1
            elif what == "relative_import":
                level, fromlist, name = args
                if name:
                    self._safe_import_hook(name, m, fromlist, level=level)
                else:
                    parent = self.determine_parent(m, level=level)
                    # m is still the caller here... [bp]
                    self._safe_import_hook(parent.__name__, m, fromlist, level=0)
            else:
                # We don't expect anything else from the generator.
                raise RuntimeError(what)

        for c in co.co_consts:
            if isinstance(c, type(co)):
                self.scan_code(c, m)
