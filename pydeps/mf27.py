import sys
import time
import struct
# from .mf.mf_next import *     # for debugging next version
import modulefinder
from modulefinder import (
    ModuleFinder as NativeModuleFinder
)
from importlib.util import MAGIC_NUMBER
import marshal
import dis
from . import mfimp

HAVE_ARGUMENT = dis.HAVE_ARGUMENT

# from stdlib's modulefinder
_PY_SOURCE = mfimp.PY_SOURCE
_PY_COMPILED = mfimp.PY_COMPILED
_PKG_DIRECTORY = mfimp.PKG_DIRECTORY

# monkey-patch broken modulefinder._find_module
# (https://github.com/python/cpython/issues/84530)
# in Python 3.8-3.10
if hasattr(modulefinder, '_find_module'):
    modulefinder._find_module = mfimp.find_module


def load_pyc(fp, mf=None):
    """Load a pyc file from a file object.
    """
    # adapted from https://github.com/nedbat/coveragepy/blob/master/lab/show_pyc.py#L21
    data = fp.read()
    pos = 0
    if data[:4] != MAGIC_NUMBER:
        raise ImportError("Bad magic number in .pyc file")

    pos += 4
    read_date_and_size = True
    if sys.version_info >= (3, 7):
        # 3.7 added a flags word
        flags = struct.unpack('<L', data[4:8])[0]
        pos += 4
        hash_based = bool(flags & 0x01)
        # check_source = bool(flags & 0x02)
        if hash_based:
            source_hash = data[pos:pos + 8]
            pos += 8
            read_date_and_size = False
            # print(f"hash {binascii.hexlify(source_hash)}")
            # print(f"check_source {check_source}")
    if read_date_and_size:
        moddate = data[pos:pos + 4]
        pos += 4
        # modtime = time.asctime(time.localtime(struct.unpack('<L', moddate)[0]))
        # print(f"moddate {binascii.hexlify(moddate)} ({modtime})")
        size = data[pos:pos + 4]
        pos += 4
        # size = fp.read(4)
        # print("pysize %s (%d)" % (binascii.hexlify(size), struct.unpack('<L', size)[0]))
    assert len(data) >= pos
    co = marshal.loads(data[pos:])
    return co


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
            _PKG_DIRECTORY: 'PKG_DIRECTORY',
            _PY_SOURCE: 'PY_SOURCE',
            _PY_COMPILED: 'PY_COMPILED',
        }.get(kind, 'unknown-kind')
        self.msgin(2, "load_module(%s) fqname=%s, fp=%s, pathname=%s" % (kstr, fqname, fp and "fp", pathname))

        if kind == _PKG_DIRECTORY:
            module = self.load_package(fqname, pathname)
            self.msgout(2, "load_module ->", module)
            return module

        if kind == _PY_SOURCE:
            txt = fp.read()
            txt += b'\n' if isinstance(txt, bytes) else '\n'
            co = compile(
                txt,
                pathname,
                'exec',            # compile code block
                dont_inherit=True  # [pydeps] don't inherit future statements from current environment
            )

        elif kind == _PY_COMPILED:
            # (see issue #191)
            try:
                co = load_pyc(fp, self)
            except ImportError:
                self.msgout(2, "raise ImportError: Bad magic number", pathname)
                raise ImportError("Bad magic number in %s" % pathname)

            # if fp.read(4) != MAGIC_NUMBER:
            #     self.msgout(2, "raise ImportError: Bad magic number", pathname)
            #     raise ImportError("Bad magic number in %s" % pathname)
            # fp.read(4)   # skip modification timestamp
            # co = marshal.load(fp)  # load marshalled code object.



            # adapted from https://github.com/nedbat/coveragepy/blob/master/lab/show_pyc.py#L21
            # if fp.read(4) != MAGIC_NUMBER:
            #     self.msgout(2, "raise ImportError: Bad magic number", pathname)
            #     raise ImportError("Bad magic number in %s" % pathname)

            # read_date_and_size = True
            # if sys.version_info >= (3, 7):
            #     # 3.7 added a flags word
            #     flags = struct.unpack('<L', fp.read(4))[0]
            #     hash_based = bool(flags & 0x01)
            #     check_source = bool(flags & 0x02)
            #     # print(f"flags 0x{flags:08x}")
            #     if hash_based:
            #         source_hash = fp.read(8)
            #         read_date_and_size = False
            #         # print(f"hash {binascii.hexlify(source_hash)}")
            #         # print(f"check_source {check_source}")
            # if read_date_and_size:
            #     moddate = fp.read(4)
            #     modtime = time.asctime(time.localtime(struct.unpack('<L', moddate)[0]))
            #     # print(f"moddate {binascii.hexlify(moddate)} ({modtime})")
            #     size = fp.read(4)
            #     # print("pysize %s (%d)" % (binascii.hexlify(size), struct.unpack('<L', size)[0]))
            # co = marshal.load(fp)

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
