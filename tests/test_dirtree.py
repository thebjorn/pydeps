# -*- coding: utf-8 -*-
from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps
import pytest


@pytest.mark.skip(reason="TODO: fix this (issue #174)")
def test_dirtree():
    files = """
        foo:
            - a:
                - __init__.py: ''
                - a.py: |
                    from b.b import bval
            - b:
                - __init__.py: ''
                - b.py: |
                    bval = 42
    """
    with create_files(files) as workdir:
        assert simpledeps('foo', '--show-deps -LINFO -vv') == {
            'b.b -> a.a',
        }
