from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_cycle():
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import a
    """
    with create_files(files, cleanup=False) as workdir:
        print("WORKDIR:", workdir)
        deps = simpledeps('relimp')
        assert 'relimp.a -> relimp.b' in deps
        assert 'relimp.b -> relimp.a' in deps


def test_show_cycles_filters_to_cycle_nodes():
    # a <-> b is a cycle; c sits outside it. --show-cycles should drop c.
    files = """
        relimp:
            - __init__.py
            - a.py: |
                from . import b
            - b.py: |
                from . import a
            - c.py: |
                from . import a
    """
    with create_files(files) as workdir:
        full = simpledeps('relimp')
        assert 'relimp.a -> relimp.b' in full
        assert 'relimp.b -> relimp.a' in full
        assert any('relimp.c' in edge for edge in full)

        cycles = simpledeps('relimp', '--show-cycles')
        assert 'relimp.a -> relimp.b' in cycles
        assert 'relimp.b -> relimp.a' in cycles
        assert not any('relimp.c' in edge for edge in cycles)
