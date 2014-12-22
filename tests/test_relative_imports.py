# -*- coding: utf-8 -*-
import os
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


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
        assert simpledeps('relimp') == [
            'relimp.c -> relimp.b',
            'relimp.b -> relimp.a',
        ]


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
        assert simpledeps('pdeps') == [
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
        assert simpledeps('relimp') == [
            'relimp.b.bmodule -> relimp.a.amodule'
        ]











