# -*- coding: utf-8 -*-
import sys
from tests.filemaker import create_files
from tests.simpledeps import simpledeps
import pytest


@pytest.mark.skipif(sys.platform != 'win32', reason=".pyw files only exist on windows")
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
            'foo.a -> baz.pyw',
            'foo -> baz.pyw',
            'bar -> baz.pyw',
            'bar -> foo.a',
        }
