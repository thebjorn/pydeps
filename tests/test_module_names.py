"""Targets can be given as importable module names, not just paths.

   See https://github.com/thebjorn/pydeps/issues/284
"""
import importlib
import os
import sys
from contextlib import contextmanager

import pytest

from pydeps.target import Target, resolve_modname
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


@contextmanager
def importable(*dirnames):
    """Put ``dirnames`` (relative to cwd) on sys.path, as an install would.
    """
    dirs = [os.path.abspath(d) for d in dirnames]
    sys.path[:0] = dirs
    importlib.invalidate_caches()
    try:
        yield
    finally:
        for d in dirs:
            sys.path.remove(d)


def test_package_by_name():
    files = """
        site-packages:
            - foo:
                - __init__.py
                - a.py: |
                    from foo import b
                - b.py: |
                    b = 42
    """
    with create_files(files):
        with importable('site-packages'):
            # note that we're _not_ standing in site-packages, so 'foo'
            # can only be found by importing it.
            assert simpledeps('foo', '--show-deps') == {
                'foo.b -> foo.a',
            }


def test_dotted_module_name():
    files = """
        site-packages:
            - foo:
                - __init__.py
                - a.py: |
                    from math import pi
    """
    with create_files(files):
        with importable('site-packages'):
            # a single module is analyzed in-situ, so the node is named
            # after the file (same as `pydeps site-packages/foo/a.py`).
            assert simpledeps('foo.a', '--show-deps --pylib') == {
                'math -> a.py',
            }


def test_single_file_module_by_name():
    files = """
        site-packages:
            - solo.py: |
                from math import pi
    """
    with create_files(files):
        with importable('site-packages'):
            assert simpledeps('solo', '--show-deps --pylib') == {
                'math -> solo.py',
            }


def test_namespace_package_by_name():
    files = """
        site-packages:
            - foo:
                - a.py: |
                    from math import pi
    """
    with create_files(files):
        with importable('site-packages'):
            assert simpledeps('foo', '--show-deps --pylib') == {
                'math -> foo.a',
            }


def test_path_wins_over_module_name():
    """A file/directory that exists is never shadowed by an installed
       module of the same name.
    """
    files = """
        site-packages:
            - foo:
                - __init__.py
                - installed.py: |
                    from math import pi
        foo:
            - __init__.py
            - local.py: |
                from math import pi
    """
    with create_files(files):
        with importable('site-packages'):
            deps = simpledeps('foo', '--show-deps --pylib')
            assert 'math -> foo.local' in deps
            assert 'math -> foo.installed' not in deps


def test_resolve_modname_finds_package():
    files = """
        site-packages:
            - foo:
                - __init__.py
    """
    with create_files(files) as workdir:
        with importable('site-packages'):
            assert resolve_modname('foo') == os.path.join(
                workdir, 'site-packages', 'foo'
            )


@pytest.mark.parametrize('name', [
    'sys',                    # builtin, no source to read
    'no_such_module_xyzzy',   # not importable at all
    'scikit-learn',           # not a legal dotted name
    'foo/bar',                # a path, not a module name
    '',
    'math.foo',               # parent isn't a package (find_spec raises)
    'json.nope.deep',         # ..and the parent isn't importable either
])
def test_resolve_modname_gives_up(name):
    assert resolve_modname(name) is None


def test_unresolvable_name_exits(capsys):
    with create_files("empty"):
        with pytest.raises(SystemExit):
            Target('no_such_module_xyzzy')
    assert 'no module named' in capsys.readouterr().err


def test_builtin_name_says_why(capsys):
    with create_files("empty"):
        with pytest.raises(SystemExit):
            Target('sys')
    assert 'no Python source' in capsys.readouterr().err


def test_missing_file_suggests_dotpy(capsys):
    files = """
        - foo.py: |
            from math import pi
    """
    with create_files(files):
        with pytest.raises(SystemExit):
            Target('foo')
    assert 'did you mean' in capsys.readouterr().err


class EditableFinder:
    """Stand-in for the meta-path hook that ``pip install -e`` installs.

       Such packages are invisible to ``PathFinder`` (they aren't on
       sys.path at all), so they exercise the ``find_spec`` fallback.
    """
    def __init__(self, name, location):
        self.name = name
        self.location = location

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self.name:
            return None
        return importlib.util.spec_from_file_location(
            fullname,
            os.path.join(self.location, '__init__.py'),
            submodule_search_locations=[self.location],
        )


@contextmanager
def editable_install(name, location):
    finder = EditableFinder(name, os.path.abspath(location))
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)


def test_editable_install_by_name():
    files = """
        elsewhere:
            - foo:
                - __init__.py
                - a.py: |
                    from math import pi
    """
    with create_files(files) as workdir:
        with editable_install('foo', 'elsewhere/foo'):
            # 'elsewhere' is deliberately *not* on sys.path
            assert resolve_modname('foo') == os.path.join(
                workdir, 'elsewhere', 'foo'
            )
            assert simpledeps('foo', '--show-deps --pylib') == {
                'math -> foo.a',
            }
