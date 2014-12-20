# -*- coding: utf-8 -*-
import os
from tests.filemaker import create_files
from tests.simpledeps import simpledeps, depgrf


def test_skip_modules():
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
        assert simpledeps('relimp', '-x relimp.c') == [
            'relimp.b -> relimp.a'
        ]
        # g = depgrf('relimp', '-x relimp.c relimp.b')
        # print g
        # print simpledeps('relimp', '-x relimp.c relimp.b')
        # assert 1
        # assert g == 42
