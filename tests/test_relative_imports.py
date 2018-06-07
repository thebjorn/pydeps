# -*- coding: utf-8 -*-
import os
import sys
from tests.filemaker import create_files
from tests.simpledeps import simpledeps
import pytest

def test_relative_imports():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('relimp') == ['relimp.b -> relimp.a']


def test_relative_imports2():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        deps = simpledeps('relimp')
        assert 'relimp.c -> relimp.b' in deps
        assert 'relimp.b -> relimp.a' in deps


def test_relative_imports3():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from .b import c
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('relimp') == ['relimp.b -> relimp.a']

@pytest.mark.skipif(sys.version_info < (3,), reason="implicit relative import is valid in py2")
def test_relative_imports_same_name_with_std():
    files = """
        relimp:
            - __init__.py
            - io.py: |
                import io
    """
    with create_files(files) as workdir:
        assert simpledeps('relimp', '--pylib') == ['io -> relimp.io']


def test_pydeps_colors():
    files = """
        pdeps:
            - __init__.py
            - colors.py: |
                import colorsys
            - depgraph.py: |
                import json
                import pprint
                import enum
                from . import colors
    """
    with create_files(files, cleanup=False) as workdir:
        assert simpledeps('pdeps', '-x enum') == [
            'pdeps.colors -> pdeps.depgraph',
        ]


def test_hierarchy():
    files = """
        relimp:
            - __init__.py
            - a:
                - __init__.py
                - amodule.py: |
                    from ..b import bmodule
            - b:
                - __init__.py
                - bmodule.py

    """
    with create_files(files, cleanup=True) as workdir:
        os.system("tree " + workdir)
        deps = simpledeps('relimp')
        assert 'relimp.b -> relimp.a.amodule' in deps
        assert 'relimp.b.bmodule -> relimp.a.amodule' in deps
