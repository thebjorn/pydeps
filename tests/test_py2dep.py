# -*- coding: utf-8 -*-
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_py2depgraph(capsys):
    files = """
        - a.py: |
            import b
        - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('a.py') == ['b -> a']

