# -*- coding: utf-8 -*-
# Tests for PR #242: pattern-based import-time module exclusion.
import pytest

from pydeps.py2depgraph import Excluder, MyModuleFinder


def test_excluder_empty():
    ex = Excluder([])
    assert ex('foo') is False
    assert ex('foo.bar') is False


def test_excluder_exact_name():
    ex = Excluder(['foo'])
    assert ex('foo') is True
    assert ex('bar') is False
    # exact pattern does not match submodules
    assert ex('foo.bar') is False


def test_excluder_glob_matches_submodules():
    ex = Excluder(['foo.*'])
    assert ex('foo.bar') is True
    assert ex('foo.bar.baz') is True
    assert ex('bar') is False
    # fnmatch.translate('foo.*') requires the dot + at least one char
    assert ex('foo') is False


def test_excluder_multiple_patterns():
    ex = Excluder(['foo.*', 'baz'])
    assert ex('foo.bar') is True
    assert ex('baz') is True
    assert ex('quux') is False


def test_excluder_caches_positive_hits():
    ex = Excluder(['foo.*'])
    assert 'foo.bar' not in ex._excluded
    ex('foo.bar')
    assert 'foo.bar' in ex._excluded
    # second call returns True via the cache branch
    assert ex('foo.bar') is True


def test_my_module_finder_exposes_excluder():
    mf = MyModuleFinder([], excludes=['foo.*'])
    assert mf.excluder('foo.bar') is True
    assert mf.excluder('other') is False


def test_load_module_short_circuits_excluded_name():
    # The exclude check must run before any file operations, so passing
    # fp=None is safe — stdlib would crash on it if we reached that path.
    mf = MyModuleFinder([], excludes=['foo.*'])
    with pytest.raises(ImportError, match='excluded'):
        mf.load_module('foo.bar', None, 'nonexistent', ('', '', 0))
