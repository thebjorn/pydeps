import logging

from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import empty


def test_blank_graph_warns_with_diagnostics(caplog):
    files = """
        foo:
            - __init__.py
            - a.py: |
                import unavailable_dependency
    """
    with create_files(files):
        with caplog.at_level(logging.WARNING):
            pydeps(fname='foo', **empty('--no-show --no-output'))
    assert "No dependencies to draw for 'foo'" in caplog.text
    assert '--include-missing' in caplog.text
    assert '-LDEBUG' in caplog.text


def test_excluded_dependencies_warn(caplog):
    files = """
        foo:
            - __init__.py
            - a.py: |
                import bar
        bar:
            - __init__.py
    """
    with create_files(files):
        with caplog.at_level(logging.WARNING):
            pydeps(fname='foo', **empty('--no-show --no-output -x bar'))
    assert "No dependencies to draw for 'foo'" in caplog.text


def test_visible_dependencies_do_not_warn(caplog):
    files = """
        foo:
            - __init__.py
            - a.py: |
                import bar
        bar:
            - __init__.py
    """
    with create_files(files):
        with caplog.at_level(logging.WARNING):
            pydeps(fname='foo', **empty('--no-show --no-output'))
    assert 'No dependencies to draw' not in caplog.text


def test_json_only_does_not_warn(caplog, capsys):
    files = """
        foo:
            - __init__.py
    """
    with create_files(files):
        with caplog.at_level(logging.WARNING):
            pydeps(fname='foo', **empty('--no-dot --no-output --show-deps'))
    assert 'No dependencies to draw' not in caplog.text
    assert capsys.readouterr().out.strip().startswith('{')
