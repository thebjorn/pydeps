# -*- coding: utf-8 -*-
import os

from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_file():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert simpledeps('a.py') == set()


def test_file_pylib():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert 'collections -> a' in simpledeps('a.py', '--pylib')


def test_file_pyliball():
    files = """
        a.py: |
            import collections
    """
    with create_files(files) as workdir:
        assert 'collections -> a' in simpledeps('a.py', '--pylib --pylib-all')
