# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os
import tempfile
import shutil
import yaml
from pydeps import pydeps
from pydeps.py2depgraph import py2dep
from tests.filemaker import Filemaker


@contextmanager
def create_files(filedef, cleanup=True):
    fdef = yaml.load(filedef)
    cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        Filemaker(tmpdir, fdef)
        yield tmpdir
    finally:
        os.chdir(cwd)
        if cleanup:
            shutil.rmtree(tmpdir, ignore_errors=True)


def empty():
    args = pydeps.parse_args(['foo'])
    args.pop('fname')
    return args


def simpledeps(item):
    return ["%s -> %s" % (a.name, b.name) for a, b in py2dep('relimp', **empty())]


def test_relative_imports():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('relimp') == ['relimp.b -> relimp.a']


def test_relative_imports2():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        assert simpledeps('relimp') == [
            'relimp.c -> relimp.b',
            'relimp.b -> relimp.a',
        ]


def xtest_circular():
    files = """
        circ:
            - base.py: |
                from a import amodule
            - a:
                - amodule.py: |
                    # from ..b import bmodule
                    from circ.b import bmodule
            - b:
                - bmodule.py: |
                    # from .. import base
                    from circ import base
    """
    with create_files(files, cleanup=False) as workdir:
        os.system("tree " + workdir)
        assert simpledeps('relimp') == ['relimp.b -> relimp.a']











