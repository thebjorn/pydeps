# -*- coding: utf-8 -*-
import os

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

def test_error(capsys):
    """Test that error function prints reminder about missing inits on FileNotFoundErrors."""
    try:
        error("[Errno 2] No such file or directory: 'foo'")
    except SystemExit:
        # because error invokes sys.exit(1), we have to catch it here, otherwise the test would always fail.
        pass
    else:  # test should fail if error function doesn't raise
        assert False
    captured_stdout = capsys.readouterr().out
    assert "(Did you forget to include an __init__.py?)" in captured_stdout
