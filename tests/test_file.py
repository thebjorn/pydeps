# -*- coding: utf-8 -*-
import os
from pydeps.py2depgraph import py2dep
from pydeps.pydeps import _pydeps
from pydeps.target import Target

from tests.filemaker import create_files
from tests.simpledeps import empty, simpledeps


def test_file():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert simpledeps('a.py') == set()


def test_file_in_sub_directory():
    files = """
        foo:
            - a:
                - b.py: |
                    import c
                - c.py: ""

    """
    with create_files(files) as workdir:
        # os.chdir('foo')
        # t = Target('a/b.py')
        # with t.chdir_work():
        #     print("CURDIR:", os.getcwd(), os.listdir('.'))
        #     # deps = py2dep(t, **empty(log="DEBUG", no_dot=True, show_deps=True))
        #     deps = py2dep(t, **empty())
        #     print("DEPSx:", deps)
        #     rels = {f'{a.name} -> {b.name}' for a, b in deps}
        #     print("RELS:", rels)
        #     assert 'c -> b.py' in rels
        assert 'c -> b.py' in simpledeps('foo/a/b.py')  # , '-L DEBUG')


def test_file_in_directory():
    files = """
            - a:
                - b.py: |
                    import c
                - c.py: ""

    """
    with create_files(files) as workdir:
        assert 'c -> b.py' in simpledeps('a/b.py')


def test_file_pylib():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert 'collections -> a.py' in simpledeps('a.py', '--pylib')


def test_file_pyliball():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert 'collections -> a.py' in simpledeps('a.py', '--pylib --pylib-all')
