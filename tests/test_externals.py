# -*- coding: utf-8 -*-
import ast

from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_relative_imports(capsys):
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
        pydeps(fname='foo', externals=True)
        io = capsys.readouterr()
        assert ast.literal_eval(io.out) == ['bar']
