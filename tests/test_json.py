# -*- coding: utf-8 -*-
import json
import os
from pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps, depgrf


def test_dep2dot():
    files = """
        foo:
            - __init__.py
            - a.py: |
                import b
            - b.py
    """
    with create_files(files) as workdir:
        g = depgrf("foo")
        d = json.loads(repr(g))
        print(d)
        assert '__main__' in d['foo']['imported_by']
        assert g.sources['foo.a'] == g.sources['foo.a']
        assert str(g.sources['foo.a']).startswith('foo.a')
        assert 'foo.b' in repr(g.sources['foo.a'])
