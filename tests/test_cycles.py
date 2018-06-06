# -*- coding: utf-8 -*-
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_cycle():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import a
    """
    with create_files(files, cleanup=False) as workdir:
        print("WORKDIR:", workdir)
        assert simpledeps('relimp') == [
            'relimp.a -> relimp.b',
            'relimp.b -> relimp.a'
        ]
