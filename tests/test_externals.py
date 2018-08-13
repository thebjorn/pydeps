# -*- coding: utf-8 -*-
from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_relative_imports():
    files = """
        foo:
            - __init__.py
            - a.py: |
                from bar import b
        bar:
            - __init__.py
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('foo') == {
            'bar -> foo.a',
            'bar.b -> foo.a'
        }

        assert pydeps(fname='foo', externals=True) == ['bar']
