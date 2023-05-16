# -*- coding: utf-8 -*-
# from devtools import debug
from pydeps.cli import parse_args
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_pydeps_config_ini():
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


def test_pydeps_config_setupcfg_ini():
    files = """
        setup.cfg: |
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
        args = parse_args(['relimp'])
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']


def test_pydeps_config_json():
    files = """
        pydeps.json: |
            {
                "pydeps": {
                    "rankdir": "BT",
                    "exclude": ["a", "c"]
                }
            }
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp', '--config=pydeps.json'])
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']



def test_pydeps_config_pydeps_yaml():
    files = """
        pydeps.yml: |
            pydeps:
                rankdir: BT
                exclude: 
                    - a
                    - c
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp'])
        # debug(args)
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']


def test_pydeps_config_yaml():
    files = """
        config.yml: |
            pydeps:
                rankdir: BT
                exclude: 
                    - a
                    - c
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp', '--config=config.yml'])
        # debug(args)
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']


def test_pydeps_config_pyproject_toml():
    files = """
        pyproject.toml: |
            [tool.pydeps]
                rankdir = "BT"
                exclude = ["a", "c"]
            
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp'])
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']



def test_pydeps_config_toml():
    files = """
        config.toml: |
            [tool.pydeps]
                rankdir = "BT"
                exclude = ["a", "c"]
            
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import c
            - c.py
    """
    with create_files(files) as workdir:
        args = parse_args(['relimp', '--config=config.toml'])
        assert args['rankdir'] == "BT"
        assert args['exclude'] == ['a', 'c']
