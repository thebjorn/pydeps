# -*- coding: utf-8 -*-
import os

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
