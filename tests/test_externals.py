import ast

from pydeps.pydeps import pydeps, externals
from pydeps.target import Target
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_relative_imports(capsys):
    files = """
        foo:
            - __init__.py
            - a.py: |
                from bar import b
        bar:
            - __init__.py
            - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('foo') == {
            'bar -> foo.a',
            'bar.b -> foo.a'
        }
        pydeps(fname='foo', externals=True)
        io = capsys.readouterr()
        assert ast.literal_eval(io.out) == ['bar']


def test_externals_with_nested_sourcefile():
    files = """
        foo:
            - __init__.py
            - a.py: |
                from bar import b
        bar:
            - __init__.py
            - b.py: |
                from baz import c
        baz:
            - __init__.py
            - c.py: print('hello world')
    """
    with create_files(files):
        assert simpledeps('foo') == {
            'bar -> foo.a',
            'bar.b -> foo.a',
        }
        ext = externals(
            Target('foo/a.py', use_calling_fname=True),
            pylib_all=False,
            pylib=False,
        )
        assert "bar" in ext


def test_external_import_with_same_prefix(capsys):
    """A package-name prefix alone does not make an import internal."""
    files = """
        foo:
            - __init__.py
            - a.py: |
                from foobar import b
        foobar:
            - __init__.py
            - b.py
    """
    with create_files(files):
        assert simpledeps('foo') == {
            'foobar -> foo.a',
            'foobar.b -> foo.a',
        }
        pydeps(fname='foo', externals=True)
        assert ast.literal_eval(capsys.readouterr().out) == ['foobar']


def test_external_same_prefix_does_not_add_transitive_imports(capsys):
    """Only the target package's own imports contribute external dependencies."""
    files = """
        foo:
            - __init__.py
            - a.py: |
                from foobar import b
                from . import internal
            - internal.py
        foobar:
            - __init__.py
            - b.py: |
                import baz
        baz:
            - __init__.py
    """
    with create_files(files):
        pydeps(fname='foo', externals=True)
        assert ast.literal_eval(capsys.readouterr().out) == ['foobar']
