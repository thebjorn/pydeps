"""
Abstracting the target for pydeps to work on.
"""
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager
import importlib.util
from importlib.machinery import PathFinder
import logging
log = logging.getLogger(__name__)

SUFFIXES = ('.py', '.pyc', '.pyo', '.pyw')


def is_dotted_name(name):
    """Could ``name`` appear after an ``import`` statement?
    """
    return bool(name) and all(
        part.isidentifier() for part in name.split('.')
    )


def find_modspec(name):
    """Return the ModuleSpec for ``name``, or ``None`` if it isn't
       importable.

       We first walk the name part-by-part through ``PathFinder``, which
       only looks at the file system and thus doesn't execute any of your
       code.  That misses modules provided by a meta-path hook (notably
       ``pip install -e`` under PEP-660), so we fall back to the full
       ``find_spec`` for those.  The fallback imports parent packages of
       dotted names -- the plain ``pydeps <pkg>`` case never gets there.
    """
    paths = None       # ..which means sys.path to PathFinder
    spec = None
    for part in name.split('.'):
        try:
            spec = PathFinder.find_spec(part, paths)
        except (ImportError, ValueError):  # pragma: nocover
            spec = None
        if spec is None:
            break
        paths = list(spec.submodule_search_locations or []) or None
    else:
        return spec

    try:
        return importlib.util.find_spec(name)
    except (ImportError, AttributeError, ValueError):
        # ImportError: a parent package isn't importable after all,
        # AttributeError/ValueError: __spec__ is missing or None.
        return None


def resolve_modname(name):
    """Find the location on disk of the module/package called ``name``.

       Returns the directory of ``name`` if it is a (namespace) package,
       the file name if it is a plain module, and ``None`` if ``name``
       isn't importable (or is a builtin/extension module, which has no
       Python source for us to look at).
    """
    if not is_dotted_name(name):
        return None

    spec = find_modspec(name)
    if spec is None:
        return None

    locations = list(spec.submodule_search_locations or [])
    if locations:
        # a regular package (or the first directory of a namespace
        # package, cfr. the caveat in issue #19).
        return locations[0]
    if spec.origin and spec.origin.endswith(SUFFIXES) and os.path.exists(spec.origin):
        return spec.origin
    return None         # builtin/frozen/extension modules have no source


class Target(object):
    """The compilation target.
    """
    is_pysource = False
    is_module = False
    is_dir = False

    def __init__(self, path, **kwargs):
        """Initialise target

        Args:
            path: module path

        Keyword Args:
            use_calling_fname (bool): flag to use the `calling_fname` instead of `fname` in `self.get_src_fname`
        """

        # log.debug("CURDIR: %s, path: %s, exists: %s", os.getcwd(), path, os.path.exists(path))
        # print("Target::CURDIR: %s, path: %s, exists: %s" % (os.getcwd(), path, os.path.exists(path)))

        self.calling_fname = path
        self.calling_dir = os.getcwd()
        self.exists = os.path.exists(path)
        self.use_calling_fname = kwargs.get('use_calling_fname', False)

        if not self.exists:
            # `path` doesn't name a file or a directory, so it might be an
            # importable module/package instead (`pydeps pandas`).  Paths
            # win when both would match, so this is only ever a fallback.
            modname_path = resolve_modname(path)
            if modname_path is not None:
                log.debug("resolved module name %r to %r", path, modname_path)
                # use the resolved (absolute) location from here on, so
                # that everything downstream sees a plain old path.
                self.calling_fname = path = modname_path
                self.exists = True

        if self.exists:
            self.path = os.path.realpath(path)
        else:
            print("No such file or directory:", repr(path), file=sys.stderr)
            if os.path.exists(path + '.py'):
                print("..did you mean:", path + '.py', '?', file=sys.stderr)
            elif is_dotted_name(path):
                if find_modspec(path) is not None:
                    print("..", repr(path), "is importable, but has no Python",
                          "source for pydeps to read", file=sys.stderr)
                    print("  (builtin, frozen, and C extension modules can't",
                          "be analyzed).", file=sys.stderr)
                else:
                    print("..and no module named", repr(path), "is importable",
                          file=sys.stderr)
                    print("  (is it installed in the current environment?)",
                          file=sys.stderr)
            sys.exit(1)
        self.is_dir = os.path.isdir(self.path)
        self.is_module = self.is_dir and '__init__.py' in os.listdir(self.path)
        self.is_pysource = os.path.splitext(self.path)[1] in SUFFIXES
        self.fname = os.path.basename(self.path)
        if self.is_dir:
            self.dirname = self.fname
            self.modname = self.fname
        else:
            self.dirname = os.path.dirname(self.path)
            self.modname = os.path.splitext(self.fname)[0]

        if self.is_pysource:
            # we will work directly on the file (in-situ)
            self.workdir = os.path.dirname(self.path)
        else:
            self.workdir = os.path.realpath(tempfile.mkdtemp())

        self.syspath_dir = self.get_package_root()
        # split path such that syspath_dir + relpath == path
        self.relpath = self.path[len(self.syspath_dir):].lstrip(os.path.sep)
        if self.is_dir:
            self.modpath = self.relpath.replace(os.path.sep, '.')
        else:
            self.modpath = os.path.splitext(self.relpath)[0].replace(os.path.sep, '.')
        for part in self.modpath.split('.'):
            if not part.isidentifier():
                print(
                    "Cannot analyze {!r}: {!r} is not a valid Python "
                    "module name.".format(self.calling_fname, part),
                    file=sys.stderr,
                )
                print(
                    "\nTechnical reason:\n"
                    "  pydeps works by generating a synthetic 'dummy' module\n"
                    "  (e.g. _dummy_<target>.py) that contains real Python\n"
                    "  'import <modname>' statements for every submodule of\n"
                    "  the target, then runs Python's modulefinder on that\n"
                    "  dummy to trace the import graph. The 'import' keyword\n"
                    "  is part of Python's grammar and only accepts dotted\n"
                    "  identifiers -- letters, digits, and underscores, and\n"
                    "  not starting with a digit. A name like {!r} cannot\n"
                    "  appear on the right-hand side of an import statement,\n"
                    "  so modulefinder has nothing to trace and pydeps\n"
                    "  produces an empty graph.\n"
                    "\nFix:\n"
                    "  Rename the offending file or directory so that every\n"
                    "  path component is a valid Python identifier (e.g.\n"
                    "  replace '-' with '_'). If the file must keep its\n"
                    "  on-disk name, point pydeps at a package whose name\n"
                    "  is importable instead.".format(part),
                    file=sys.stderr,
                )
                sys.exit(1)
        self.package_root = os.path.join(
            self.syspath_dir,
            self._path_parts(self.relpath)[0]
        )

    def get_src_fname(self):
        """Return the source file name to use."""
        log.debug("[get_src_fname] use_calling_name: %s", self.use_calling_fname)

        return self.calling_fname if self.use_calling_fname else self.fname

    @contextmanager
    def chdir_work(self):
        try:
            os.chdir(self.workdir)
            sys.path.insert(0, self.syspath_dir)
            yield
        finally:
            os.chdir(self.calling_dir)
            if sys.path[0] == self.syspath_dir:
                sys.path = sys.path[1:]
            self.close()

    def get_package_root(self):
        for d in self.get_parents():
            if '__init__.py' not in os.listdir(d):
                return d

        raise Exception(
            "do you have an __init__.py file at the "
            "root of the drive..?")  # pragma: nocover

    def get_parents(self):
        def _parent_iter():
            parts = self._path_parts(self.path)
            for i in range(1, len(parts)):
                yield os.path.join(*parts[:-i])
        return list(_parent_iter())

    def _path_parts(self, pth):
        """Return a list of all directories in the path ``pth``.
        """
        res = re.split(r"[\\/]", pth)
        if res and os.path.splitdrive(res[0]) == (res[0], ''):
            res[0] += os.path.sep
        return res

    def __del__(self):
        self.close()

    def close(self):
        """Clean up after ourselves.
        """
        try:
            # make sure we don't delete the user's source file if we're working
            # on it in-situ.
            if not self.is_pysource and hasattr(self, 'workdir'):
                shutil.rmtree(self.workdir)
        except OSError:
            pass

    def __repr__(self):  # pragma: nocover
        return json.dumps(
            {k: v for k, v in self.__dict__.items() if not k.startswith('_')},
            indent=4, sort_keys=True
        )
