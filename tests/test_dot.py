# -*- coding: utf-8 -*-
from pydeps.dot import dot


def test_svg(tmpdir):
    tmpdir.chdir()
    ab = tmpdir.join('ab.svg')
    dot(u"""
    digraph G {
        a -> b
    }
    """, o=ab.basename)
    assert ab.exists()


def test_svg_str(tmpdir):
    tmpdir.chdir()
    ab = tmpdir.join('ab.svg')
    dot("""
    digraph G {
        a -> b
    }
    """, o=ab.basename)
    assert ab.exists()
