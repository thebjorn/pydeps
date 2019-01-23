# -*- coding: utf-8 -*-
from pydeps.render_context import RenderContext


def test_render_context():
    ctx = RenderContext()
    with ctx.graph():
        ctx.write_rule('a', 'b')
    assert 'a -> b' in ctx.text()
    assert 'b -> a' not in ctx.text()
    assert 'rankdir = TB' in ctx.text()

def test_render_context_reverse():
    ctx = RenderContext(reverse=True)
    with ctx.graph():
        ctx.write_rule('a', 'b')
    assert 'b -> a' in ctx.text()
    assert 'a -> b' not in ctx.text()
    assert 'rankdir = BT' in ctx.text()

def test_render_context_rankdir():
    ctx = RenderContext()
    with ctx.graph(rankdir='LR'):
        pass
    assert 'rankdir = LR' in ctx.text()