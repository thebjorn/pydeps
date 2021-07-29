# -*- coding: utf-8 -*-
import os
import logging
from unittest.mock import patch, call

from pydeps.cli import error
from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps, empty


def test_output(tmpdir):
    files = """
        unrelated: []
        foo:
            - __init__.py
            - a.py: |
                from bar import b
        bar:
            - __init__.py
            - b.py
    """
    with create_files(files) as workdir:
        assert os.getcwd() == workdir

        outname = os.path.join('unrelated', 'foo.svg')
        assert not os.path.exists(outname)
        pydeps(fname='foo', **empty('--noshow', output=outname))
        assert os.path.exists(outname)

@patch('sys.exit')
@patch('builtins.print')
def test_error(mocked_print, mocked_sys_exit):
    """Test that error function prints reminder about missing inits on FileNotFoundErrors."""
    error("[Errno 2] No such file or directory: 'foo'")
    mocked_print.assert_called_with("\t(Did you forget to include an __init__.py?)")
