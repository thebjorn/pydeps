# -*- coding: utf-8 -*-


from StringIO import StringIO
from contextlib import contextmanager
import textwrap


class RenderContext(object):
    def __init__(self, out=None):
        self.out = out
        self.fp = StringIO()
        self.fillcolor = '#ffffff'
        self.fontcolor = '#000000'
        self.name = None
        self.concentrate = None

    @contextmanager
    def graph(self, **kw):
        """Set up a graphviz graph context.
        """
        self.name = kw.get('name', 'G')
        self.fillcolor = kw.get('fillcolor', '#ffffff')
        self.fontcolor = kw.get('fontcolor', '#000000')
        if kw.get('concentrate', True):
            self.concentrate = 'concentrate = true;'
        else:
            self.concentrate = ''
        self.dedent("""
            digraph {self.name} {{
                {self.concentrate}
                node [style=filled,fillcolor="{self.fillcolor}",fontcolor="{self.fontcolor}",fontname=Helvetica,fontsize=10];

        """.format(self=self))
        yield
        self.writeln('}')

    def text(self):
        """Get value of output stream (StringIO).
        """
        if self.out:
            self.out.close()  # pragma: nocover
        return self.fp.getvalue()

    def write(self, txt):
        """Write ``txt`` to file and output stream (StringIO).
        """
        self.fp.write(txt)
        if self.out:
            self.out.write(txt)  # pragma: nocover

    def writeln(self, txt):
        """Write ``txt`` and add newline.
        """
        self.write(txt + '\n')

    def dedent(self, txt):
        """Write ``txt`` dedented.
        """
        self.write(textwrap.dedent(txt))

    def write_attributes(self, attrs):
        """Write comma separated attribute values (if exists).
        """
        if attrs:
            self.write(
                ' ['
                + ','.join('%s="%s"' % kv for kv in attrs.items())
                + ']'
            )
        else:  # pragma: nocover
            pass

    def _nodename(self, x):
        "Return a valid node name."
        return x.replace('.', '_')

    def _delattr(self, attr, key, value):
        if attr.get(key) == value:
            del attr[key]

    def write_rule(self, a, b, **attrs):
        "a -> b [a1=x,a2=y];"
        with self.rule():
            self.write('%s -> %s' % (self._nodename(a), self._nodename(b)))
            self._delattr(attrs, 'weight', 1)
            self._delattr(attrs, 'minlen', 1)
            self.write_attributes(attrs)

    def write_node(self, a, **attrs):
        "a [a1=x,a2=y];"
        with self.rule():
            nodename = self._nodename(a)
            self.write(nodename)
            self._delattr(attrs, 'label', nodename)
            self._delattr(attrs, 'fillcolor', self.fillcolor)
            self._delattr(attrs, 'fontcolor', self.fontcolor)
            self.write_attributes(attrs)

    @contextmanager
    def rule(self):
        """Write indented rule.
        """
        self.write('    ')
        yield
        self.writeln(';')
