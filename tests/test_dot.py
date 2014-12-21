# -*- coding: utf-8 -*-
from pydeps.dot import dot, cmd2args


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


def test_boolopt(tmpdir):
    tmpdir.chdir()
    ab = tmpdir.join('ab.svg')
    dot("""
    digraph G {
        a -> b
    }
    """, x=True, o=ab.basename)
    print tmpdir.listdir()
    assert ab.exists()


def test_obj(tmpdir):
    class MyClass(object):
        def __unicode__(self):
            return u"""
                digraph G {
                    a -> b
                }
                """

    tmpdir.chdir()
    ab = tmpdir.join('ab.svg')
    dot(MyClass(), x=True, o=ab.basename)
    print tmpdir.listdir()
    assert ab.exists()


def test_cmd2args():
    assert cmd2args([1, 2]) == [1, 2]
