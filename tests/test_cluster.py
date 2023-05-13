import os
from pydeps.cli import parse_args
from pydeps.pydeps import pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_cluster():
    files = """
        - bar_module:
            - __init__.py: ''
            - bar_a:
                - __init__.py: ''
                - a.py: |
                    from bar_module.bar_a import aa
                - aa.py: ''
            - bar_b:
                - __init__.py: ''
                - b.py: from bar_module.bar_a import aa
            - bar_c:
                - __init__.py: ''
                - c.py: |
                    from bar_module.bar_a import a
        - foo_module:
            - __init__.py: ''
            - foo_a:
                - __init__.py: ''
                - a.py: |
                    from . import aa
                - aa.py: ''
            - foo_c:
                - __init__.py: ''
                - c.py: |-
                    from foo_module.foo_a import aa
                    from bar_module.bar_c import c
    """
    with create_files(files) as workdir:
        args = parse_args(['foo_module', '--no-config', '--show-deps', '--cluster', '--max-cluster-size=100',
                           '--show-dot', '--dot-output', 'output.dot', '--no-show', '-LINFO', '-vv'])
        pydeps(**args)
        assert 'output.dot' in os.listdir(workdir)
        dot_output = open('output.dot').read()

        assert 'subgraph cluster_bar_module' in dot_output
        assert 'ltail="cluster_bar_module"' in dot_output
