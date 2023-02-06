# -*- coding: utf-8 -*-
from pydeps.cli import parse_args
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_pydeps_config_file():
    files = """
        config.ini: |
            [pydeps]
            rankdir = BT
            exclude = 
                a
                c
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp', '--config=config.ini'])
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']
