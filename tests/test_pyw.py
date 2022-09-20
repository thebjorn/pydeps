# -*- coding: utf-8 -*-
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_from_pyw():
    files = """
        baz.pyw: |
            import foo.a
            import bar
        foo:
            - __init__.py
            - a.py: |
                from bar import py
        bar:
            - __init__.py
    """
    with create_files(files) as workdir:
        assert simpledeps('baz.pyw', '--show-deps -LINFO -vv') == {
            'foo.a -> baz',
            'foo -> baz',
            'bar -> baz',
            'bar -> foo.a',
        }
