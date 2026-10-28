"""Path-based filtering for issue #237, using real module discovery."""
import json
import os
import sys

import pytest

from pydeps.cli import parse_args
from pydeps.depgraph import DepGraph
from pydeps.py2depgraph import py2dep
from pydeps.target import Target
from tests.filemaker import create_files
from tests.simpledeps import empty


PROJECT = """
    - main.py: |
        import first.a
        import second.c
    - first:
        - __init__.py
        - a.py: |
            from . import b
        - b.py: |
            from . import leaf
        - leaf.py
    - second:
        - __init__.py
        - c.py: |
            import stdlib_list
"""


def graph_for(item, **options):
    target = Target(item)
    with target.chdir_work():
        return py2dep(target, **empty('--max-bacon=0', **options))


def edges(graph):
    return {(a.name, b.name) for a, b in graph}


def test_file_keeps_internal_chain_and_removes_installed_package():
    with create_files(PROJECT):
        graph = graph_for('main.py', internal_only=True)
        assert set(graph.sources) == {
            'main.py', 'first', 'first.a', 'first.b', 'first.leaf', 'second', 'second.c',
        }
        assert ('first.a', 'main.py') in edges(graph)
        assert ('first.b', 'first.a') in edges(graph)
        assert ('first.leaf', 'first.b') in edges(graph)
        for source in graph.sources.values():
            assert set(source.imports) <= set(graph.sources)
            assert set(source.imported_by) <= set(graph.sources)


def test_default_still_includes_external_dependencies():
    with create_files(PROJECT):
        graph = graph_for('main.py')
        assert ('stdlib_list', 'second.c') in edges(graph)
        assert ('first.leaf', 'first.b') in edges(graph)


@pytest.mark.parametrize('item, entry, internal_module', [
    ('main.py', 'main.py', 'first.leaf'),
    ('second', '__main__', 'second.c'),
])
def test_raw_output_respects_internal_boundary_without_changing_graph(
        capsys, item, entry, internal_module):
    with create_files(PROJECT):
        expected = graph_for(item, internal_only=True, max_bacon=1)
        actual = graph_for(item, internal_only=True, show_raw_deps=True, max_bacon=1)
        raw = json.loads(capsys.readouterr().out)
        assert 'stdlib_list' not in raw
        assert internal_module in raw
        assert json.loads(actual.__json__()) == json.loads(expected.__json__())
        if entry == '__main__':
            assert raw[entry]['excluded'] == 'EXCLUDED'
            assert entry not in actual.sources
        else:
            assert entry in actual.sources
            assert internal_module not in actual.sources

        graph_for(item, show_raw_deps=True, max_bacon=1)
        unfiltered_raw = json.loads(capsys.readouterr().out)
        assert 'stdlib_list' in unfiltered_raw


@pytest.mark.parametrize('options, present, absent', [
    ({'max_bacon': 1}, 'first.a', 'first.b'),
    ({'only': ['first']}, 'first.b', 'second.c'),
    ({'exclude': ['first.b']}, 'first.a', 'first.b'),
    ({'exclude_exact': ['first.b']}, 'first.a', 'first.b'),
])
def test_combines_with_existing_filters(options, present, absent):
    with create_files(PROJECT):
        graph = graph_for('main.py', internal_only=True, **options)
        assert present in graph.sources
        assert absent not in graph.sources
        assert 'stdlib_list' not in graph.sources


def test_directory_boundary_does_not_include_similar_prefix(monkeypatch):
    files = """
        - app:
            - __init__.py
            - a.py: |
                from . import b
                import app_vendor.c
            - b.py
        - app_vendor:
            - __init__.py
            - c.py
    """
    with create_files(files) as workdir:
        monkeypatch.syspath_prepend(workdir)
        assert ('app_vendor.c', 'app.a') in edges(graph_for('app'))
        graph = graph_for('app', internal_only=True)
        assert set(graph.sources) == {'app', 'app.a', 'app.b'}
        assert edges(graph) == {('app.b', 'app.a')}


def test_importable_package_uses_resolved_target(monkeypatch):
    files = """
        - installed:
            - app:
                - __init__.py
                - a.py: |
                    from . import b
                    import stdlib_list
                - b.py
    """
    with create_files(files) as workdir:
        monkeypatch.syspath_prepend(os.path.join(workdir, 'installed'))
        graph = graph_for('app', internal_only=True)
        assert edges(graph) == {('app.b', 'app.a')}


def test_namespace_children_with_known_paths_survive():
    files = """
        - ns:
            - a.py: |
                from ns import b
                import stdlib_list
            - b.py
    """
    with create_files(files):
        graph = graph_for('ns', internal_only=True)
        assert set(graph.sources) == {'ns.a', 'ns.b'}
        assert edges(graph) == {('ns.b', 'ns.a')}


def raw_graph(tmp_path, imports, **options):
    main = tmp_path / 'project' / 'main.py'
    main.parent.mkdir(exist_ok=True)
    main.touch()
    target = Target(str(main))
    return DepGraph({'__main__': imports}, {}, target,
                    **empty('--max-bacon=0', dummyname=target.fname,
                            internal_only=True, **options))


def test_unknown_paths_are_excluded_even_with_include_missing(tmp_path):
    graph = raw_graph(tmp_path, {'missing': None}, include_missing=True)
    assert set(graph.sources) == {'main.py'}
    assert edges(graph) == set()


def test_path_components_and_parent_traversal(tmp_path):
    root = tmp_path / 'project'
    graph = raw_graph(tmp_path, {
        'inside': str(root / 'child.py'),
        'neighbor': str(tmp_path / 'project_vendor' / 'child.py'),
        'escape': str(root / '..' / 'outside.py'),
    })
    assert set(graph.sources) == {'main.py', 'inside'}
    assert edges(graph) == {('inside', 'main.py')}


@pytest.mark.skipif(sys.platform != 'win32', reason='native Windows path semantics')
def test_windows_case_separators_and_other_drives(tmp_path):
    root = tmp_path / 'project'
    other_drive = 'Z:' if root.drive.upper() != 'Z:' else 'Y:'
    graph = raw_graph(tmp_path, {
        'inside': str(root / 'child.py').upper().replace('\\', '/'),
        'other_drive': other_drive + '/project/child.py',
    })
    assert set(graph.sources) == {'main.py', 'inside'}


@pytest.mark.skipif(sys.platform == 'win32', reason='native POSIX case semantics')
def test_posix_case_is_significant(tmp_path):
    graph = raw_graph(tmp_path, {
        'inside': str(tmp_path / 'project' / 'child.py'),
        'different_case': str(tmp_path / 'PROJECT' / 'child.py'),
    })
    assert set(graph.sources) == {'main.py', 'inside'}


def test_symlink_destinations_determine_membership(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()
    internal = root / 'internal.py'
    internal.touch()
    external = tmp_path / 'external.py'
    external.touch()
    try:
        (root / 'escape.py').symlink_to(external)
        (tmp_path / 'alias.py').symlink_to(internal)
    except OSError as error:
        pytest.skip('symlinks unavailable: %s' % error)
    graph = raw_graph(tmp_path, {
        'escape': str(root / 'escape.py'),
        'alias': str(tmp_path / 'alias.py'),
    })
    assert set(graph.sources) == {'main.py', 'alias'}


def test_internal_filter_precedes_module_name_coalescing(tmp_path):
    # Namespace portions in different directories may share a dotted prefix.
    root = tmp_path / 'project'
    graph = raw_graph(tmp_path, {
        'shared.external': str(tmp_path / 'outside' / 'mod.py'),
        'shared.internal': str(root / 'mod.py'),
    }, max_module_depth=1)
    assert set(graph.sources) == {'main.py', 'shared'}
    assert graph.sources['shared'].path == str(root / 'mod.py')


def test_active_site_packages_inside_project_are_external(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    site_packages = root / '.venv' / 'lib' / 'site-packages'
    monkeypatch.setattr('site.getsitepackages', lambda: [str(site_packages)])
    graph = raw_graph(tmp_path, {
        'local': str(root / 'local.py'),
        'thirdparty': str(site_packages / 'thirdparty.py'),
    })
    assert set(graph.sources) == {'main.py', 'local'}


def test_explicit_target_inside_site_packages_is_internal(tmp_path, monkeypatch):
    monkeypatch.setattr('site.getsitepackages', lambda: [str(tmp_path)])
    graph = raw_graph(tmp_path, {'local': str(tmp_path / 'project' / 'local.py')})
    assert edges(graph) == {('local', 'main.py')}


@pytest.mark.parametrize('filename, content', [
    ('.pydeps', '[pydeps]\ninternal_only = yes\n'),
    ('setup.cfg', '[pydeps]\ninternal_only = true\n'),
    ('pyproject.toml', '[tool.pydeps]\ninternal_only = true\n'),
    ('config.json', '{"pydeps": {"internal_only": true}}'),
    ('config.yaml', 'pydeps:\n  internal_only: true\n'),
])
def test_config_enables_internal_filter(tmp_path, monkeypatch, filename, content):
    monkeypatch.chdir(tmp_path)
    (tmp_path / filename).write_text(content)
    args = parse_args(['main.py', '--config', filename])
    assert args['internal_only'] is True


def test_cli_enables_internal_filter():
    assert parse_args(['main.py', '--no-config', '--internal-only'])['internal_only'] is True


def test_config_false_does_not_enable_filter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.pydeps').write_text('[pydeps]\ninternal_only = false\n')
    assert parse_args(['main.py'])['internal_only'] is False
    assert parse_args(['main.py', '--internal-only'])['internal_only'] is True
