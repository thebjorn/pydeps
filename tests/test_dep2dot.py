# -*- coding: utf-8 -*-
import os
import sys

import pydeps.cli
from pydeps import pydeps
from pydeps.target import Target
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_dep2dot():
    files = """
        foo:
            - __init__.py
            - a.py: |
                from . import b
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('foo', '-LDEBUG -vv') == [
            'foo.b -> foo.a'
        ]

        args = pydeps.cli.parse_args(["foo", "--noshow"])
        pydeps.pydeps(**args)
        assert os.path.exists(os.path.join(workdir, 'foo.svg'))
