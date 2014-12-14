"""
# Based on original code, Copyright 2004 Toby Dickenson,
# with changes 2014 (c) Bjorn Pettersen
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import json
import sys
import getopt
import imp
from . import colors
from .render_context import RenderContext


class PyDepGraphDot(object):
    def __init__(self, colored=True):
        self.colored = colored

    def _normalize_depgraph(self, depgraph):
        """The depgraph looks like this (for each module):

                'foo': { foo's imported modules..},
                'difflib': {
                    'collections': 'c:\\python27\\Lib\\collections.py',
                    'difflib': 'c:\\python27\\Lib\\difflib.py',
                    'doctest': 'c:\\python27\\Lib\\doctest.py',
                    'functools': 'c:\\python27\\Lib\\functools.py',
                    'heapq': 'c:\\python27\\Lib\\heapq.py',
                    're': 'c:\\srv\\venv\\dev\\lib\\re.py'
                },

            this funcction goes through the collections/difflib/doctest/..
            and make sure they're keys in the depgraph.
        """
        for module_import_dict in depgraph.values():
            for module_name in module_import_dict:
                if module_name not in depgraph:
                    depgraph[module_name] = {}
        return depgraph

    def render(self, data, ctx):
        depgraph = data['depgraph']
        types = data['types']

        with ctx.graph():
            modules = self._normalize_depgraph(depgraph).items()
            for module, imports in sorted(modules):
                tk = types.get(module)
                if self.filter_modules(module, tk):
                    for imported in sorted(imports.keys()):
                        tv = types.get(imported)
                        if self.filter_modules(imported, tv) and not self.toocommon(imported, tv):
                            ctx.write_rule(imported, module, self.edge_attributes(module, imported))
                    ctx.write_node(module, self.node_attributes(module, tk))
        return ctx.text()

    def node_attributes(self, module_name, kind):
        attrs = {
            'label': self.label(module_name)
        }
        if self.colored:
            bg, fg = self.color(module_name, kind)
            attrs['fillcolor'] = bg
            attrs['fontcolor'] = fg
        if self.toocommon(module_name, kind):
            attrs['peripheries'] = 2
        return attrs

    def edge_attributes(self, k, v):
        return dict(
            weight=self.weight(k, v),
            minlen=self.alien(k, v)
        )

    def filter_modules(self, module_name, kind):
        """Return true if this module is interesting and should be drawn.
           Return false if it should be completely omitted. This is a
           default policy - please override.
        """
        if module_name in ('os', 'sys', 'qt', 'time', '__future__', 'types', 're', 'string', 'bdb', 'pdb'):
            # nearly all modules use all of these... more or less. They add nothing to
            # our diagram.
            return 0
        if module_name.startswith('encodings.'):
            return 0
        # if s == '__main__':
        #     return 0  # 1
        if self.toocommon(module_name, kind):
            # A module where we dont want to draw references _to_. Dot doesnt handle these
            # well, so it is probably best to not draw them at all.
            return 0
        return 1

    def toocommon(self, module_name, kind):
        """Return true if references to this module are uninteresting. Such
           references do not get drawn. This is a default policy - please override.
        """
        if module_name == '__main__':
            # references *to* __main__ are never interesting. omitting them means
            # that main floats to the top of the page
            return 0
        if kind == imp.PKG_DIRECTORY:
            # dont draw references to packages.
            return 1
        return 0

    def weight(self, a, b):
        """Return the weight of the dependency from a to b. Higher weights
           usually have shorter straighter edges. Return 1 if it has normal
           weight. A value of 4 is usually good for ensuring that a related
           pair of modules are drawn next to each other. This is a default
           policy - please override.
        """
        if '_' + a == b:
            return 6

        if b.split('.')[-1].startswith('_'):
            # A module that starts with an underscore. You need a special reason to
            # import these (for example random imports _random), so draw them close
            # together
            return 4
        return 1

    def alien(self, a, b):
        """Return non-zero if references to this module are strange, and
           should be drawn extra-long. the value defines the length, in
           rank. This is also good for putting some vertical space between
           seperate subsystems. This is a default policy - please override.
        """
        return 0

    def label(self, module_name):
        """Convert a module name to a formatted node label. This is a default
           policy - please override.
        """
        if len(module_name) > 14 and '.' in module_name:
            return '\\.\\n'.join(module_name.split('.'))
        return module_name

    def color(self, module_name, kind):
        """Return the node color for this module name. This is a default
           policy - please override.

           Calculate a color systematically based on the hash of the module
           name. Modules in the same package have the same color. Unpackaged
           modules are grey
        """
        t = self.normalise_module_name_for_hash_coloring(module_name, kind)
        bg = colors.name2rgb(t)
        fg = colors.foreground(bg, (255, 255, 255), (0, 0, 0))
        return colors.rgb2css(*bg), colors.rgb2css(*fg)

    def normalise_module_name_for_hash_coloring(self, module_name, kind):
        # module_name = module_name.replace('\\n', '').replace('\\', '')
        # print "MN:", module_name
        if kind == imp.PKG_DIRECTORY:
            return module_name
        else:
            i = module_name.rfind('.')
            if i < 0:
                return ''
            else:
                return module_name[:i]


def dep2dot(depgraph, color=True):
    dotter = PyDepGraphDot(colored=color)
    ctx = RenderContext()
    return dotter.render(depgraph, ctx)


def depgraph2dot():
    opts, args = getopt.getopt(sys.argv[1:], '-f:', ['mono', 'file='])

    _colored = True
    _output = sys.stdout
    for _opt, _val in opts:
        if _opt == '--mono':
            _colored = False
        if _opt in ('-f', '--file'):
            _output = open(_val, 'w')

    dotter = PyDepGraphDot(colored=_colored)
    ctx = RenderContext(_output)
    dotter.render(
        data=json.loads(sys.stdin.read()),
        ctx=ctx
    )
    _output.close()


if __name__ == '__main__':
    depgraph2dot()
