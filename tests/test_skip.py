# -*- coding: utf-8 -*-
from __future__ import print_function
from tests.filemaker import create_files
from tests.simpledeps import simpledeps, depgrf


def test_no_skip():
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
        print("plain", simpledeps('relimp'))
        assert simpledeps('relimp') == {
            'relimp.b -> relimp.a',
            'relimp.c -> relimp.b'
        }


def test_skip_module_pattern():
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
        print("-x", simpledeps('relimp', '-x relimp.*'))
        assert simpledeps('relimp', '-x relimp.*') == set()


# def test_skip_exact_pattern():
#     files = """
#         relimp:
#             - __init__.py
#             - a.py: |
#                 from . import b
#             - b.py: |
#                 from . import c
#             - c.py
#     """
#     with create_files(files) as workdir:
#         print('-xx', simpledeps('relimp', '-xx relimp.*'))
#         assert simpledeps('relimp', '-xx relimp.*') != set()


def test_skip_exact():
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
        print('-xx', simpledeps('relimp', '-xx relimp.c'))
        assert simpledeps('relimp', '-xx relimp.c') == {
            'relimp.b -> relimp.a'
        }


def test_skip_modules():
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
        assert simpledeps('relimp', '-x relimp.c') == {
            'relimp.b -> relimp.a'
        }
        # g = depgrf('relimp', '-x relimp.c relimp.b')
        # print g
        # print simpledeps('relimp', '-x relimp.c relimp.b')
        # assert 1
        # assert g == 42


def test_rawdeps():
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
        assert simpledeps('relimp', '--show-raw-deps -x relimp.c') == {
            'relimp.b -> relimp.a'
        }
