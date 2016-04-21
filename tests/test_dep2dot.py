# -*- coding: utf-8 -*-
import os
from pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_dep2dot():
    files = """
        foo:
            - __init__.py
            - a.py: |
                import b
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('foo') == [
            'foo.b -> foo.a'
        ]
        pydeps._pydeps(**pydeps.parse_args(["foo", "--noshow"]))
        assert os.path.exists(os.path.join(workdir, 'foo.svg'))
