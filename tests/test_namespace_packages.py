# Tests for issue #19: PEP 420 namespace package support.
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_namespace_package_child_is_found():
    # pkg1 is a namespace package (no __init__.py); pkg2 is regular.
    # Both children should be discoverable from main.py.
    files = """
        - main.py: |
            import pkg1.foo
            import pkg2.bar
        - pkg1:
            - foo.py
        - pkg2:
            - __init__.py
            - bar.py
    """
    with create_files(files) as workdir:
        deps = simpledeps('main.py')
        assert any('pkg1.foo' in edge for edge in deps), deps
        assert any('pkg2.bar' in edge for edge in deps), deps


def test_namespace_package_transitive_imports():
    # Transitive deps through a namespace package are followed:
    # main -> ns.foo -> ns.bar must all land in the graph.
    files = """
        - main.py: |
            import ns.foo
        - ns:
            - foo.py: |
                from . import bar
            - bar.py
    """
    with create_files(files) as workdir:
        deps = simpledeps('main.py')
        assert any('ns.foo' in edge for edge in deps), deps
        assert any('ns.bar' in edge for edge in deps), deps


def test_regular_package_shadows_namespace():
    # Per PEP 420, a regular package (with __init__.py) takes priority
    # over a namespace package of the same name. The existing __init__.py
    # path must still win.
    files = """
        - main.py: |
            import pkg.mod
        - pkg:
            - __init__.py
            - mod.py
    """
    with create_files(files) as workdir:
        deps = simpledeps('main.py')
        assert any('pkg.mod' in edge for edge in deps), deps
