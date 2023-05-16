# -*- coding: utf-8 -*-
import os
# from devtools import debug
from pydeps.pydeps import call_pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_py2depgraph(capsys):
    files = """
        - a.py: |
            import b
        - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('a.py') == {'b -> a.py'}


def test_pydeps_api():
    files = """
        - a.py: |
            import b
        - b.py
    """
    with create_files(files) as workdir:
        call_pydeps('a.py', no_show=True, show_dot=True, dot_out='a.dot')
        # debug(os.getcwd())
        # debug(os.listdir('.'))
        with open('a.dot') as f:
            dot = f.read()
            # debug(dot)
        assert 'b -> a_py' in dot
