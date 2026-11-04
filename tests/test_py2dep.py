import os
import subprocess
import sys
from pathlib import Path
# from devtools import debug
from pydeps.pydeps import call_pydeps
from tests.filemaker import create_files
from tests.simpledeps import simpledeps


def test_py2depgraph(capsys):
    files = """
        - a.py: |
            import b
        - b.py
    """
    with create_files(files) as workdir:
        assert simpledeps('a.py') == {'b -> a.py'}


def test_pydeps_api():
    files = """
        - a.py: |
            import b
        - b.py
    """
    with create_files(files) as workdir:
        call_pydeps('a.py', no_show=True, show_dot=True, dot_out='a.dot')
        # debug(os.getcwd())
        # debug(os.listdir('.'))
        with open('a.dot') as f:
            dot = f.read()
            # debug(dot)
        assert 'b -> a_py' in dot


def test_dependency_analysis_does_not_import_yaml_target(tmp_path):
    package = tmp_path / "yaml"
    package.mkdir()
    marker = tmp_path / "imported.txt"
    (package / "__init__.py").write_text(
        "open(%r, 'w').write('executed')\n"
        "def dump(*args, **kwargs):\n"
        "    return ''\n" % str(marker)
    )
    (package / "example.py").write_text("from . import sibling\n")
    (package / "sibling.py").write_text("")
    # Use a fresh interpreter: the test fixture helpers already import PyYAML.
    source_root = str(Path(__file__).resolve().parents[1])
    script = (
        "import sys; sys.path.insert(0, %r); "
        "from tests.simpledeps import simpledeps; "
        "assert 'yaml.sibling -> yaml.example' in simpledeps('yaml')"
    ) % source_root
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not marker.exists()
    assert not list(package.rglob("*.pyc"))
