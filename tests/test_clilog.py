import pytest
from pydeps import clilog


def test_default_no_verbose_output(capsys):
    clilog.reset_levels()
    clilog.verbose(1, "cow")
    captured = capsys.readouterr()
    assert not captured.out == "cow\n"


def test_verbose_output(capsys):
    clilog.reset_levels()
    clilog.set_level("verbose", 1)
    clilog.verbose(1, "cow")
    clilog.verbose(2, "dog")
    captured = capsys.readouterr()
    assert captured.out == "cow\n"

def test_verbose_output_implicit_level(capsys):
    clilog.reset_levels()
    clilog.set_level("verbose", 1)
    clilog.verbose("cow")
    captured = capsys.readouterr()
    assert captured.out == "cow\n"

def test_debug_output(capsys):
    clilog.reset_levels()
    clilog.set_level("debug", True)
    clilog.verbose(1, "cow")
    captured = capsys.readouterr()
    assert captured.out == "cow\n"


def test_hidden_verbose_output(capsys):
    clilog.reset_levels()
    clilog.set_level("verbose", 2)
    clilog.verbose(2, "cow")
    captured = capsys.readouterr()
    assert captured.out == "cow\n"


def test_verbose_output_increased_level(capsys):
    clilog.reset_levels()
    clilog.set_level("verbose", 2)
    clilog.verbose(1, "cow")
    clilog.verbose(2, "dog")
    captured = capsys.readouterr()
    assert captured.out == "cow\ndog\n"


def test_error_output(capsys):
    clilog.reset_levels()
    clilog.error("gras")
    captured = capsys.readouterr()
    assert captured.err == "ERROR: gras\n"


def test_set_level():
    clilog.reset_levels()
    clilog.set_level("verbose", 3)
    assert clilog.levels == {"verbose": 3, "debug": 0}
    clilog.set_level("debug", 4)
    assert clilog.levels == {"verbose": 3, "debug": 4}
    with pytest.raises(KeyError):
        clilog.set_level("milk", 1)
