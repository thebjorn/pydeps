# -*- coding: utf-8 -*-
from pydeps.render_context import RenderContext, Rankdir


def test_render_context():
    ctx = RenderContext()
    with ctx.graph():
        ctx.write_rule('a', 'b')
    assert 'a -> b' in ctx.text()
    assert 'b -> a' not in ctx.text()
    assert 'rankdir = TB' in ctx.text()


def test_render_context_reverse():
    # verify that rankdir is reversed in RenderBuffer, not RenderContext.
    ctx = RenderContext(reverse=True, rankdir=Rankdir.BOTTOM_TOP)
    with ctx.graph():
        ctx.write_rule('a', 'b')
    assert 'b -> a' in ctx.text()
    assert 'a -> b' not in ctx.text()
    assert 'rankdir = BT' in ctx.text()


def test_render_context_rankdir():
    ctx = RenderContext(rankdir=Rankdir.LEFT_RIGHT)
    with ctx.graph():
        pass
    text = ctx.text()
    assert 'rankdir = LR' in text
