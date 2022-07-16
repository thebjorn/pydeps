# -*- coding: utf-8 -*-
from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_from_html5lib():
    files = """
        foo:
            - __init__.py
            - a.py: |
                from bar import py
        bar:
            - __init__.py
            - py.py: |
                barpy = 42
    """
    with create_files(files) as workdir:
        assert simpledeps('foo', '--show-deps -LINFO -vv') == {
            'bar -> foo.a',
            'bar.py -> foo.a'
        }
