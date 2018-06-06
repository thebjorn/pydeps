# -*- coding: utf-8 -*-
"""
Generate requirements.txt from pydeps output...

Usage::

    pydeps <packagename> --max-bacon=0 \
           --show-raw-deps --nodot \
           --noshow | python pydeps2requirements.py

"""
import json
import sys
from collections import defaultdict

WIDTH = 80

# packages that are difficult to eliminate but shouldn't ever be part
# of a package's requirements.
skiplist = {
    '_markerlib', 'pkg_resources'
}


def dep2req(name, imported_by):
    """Convert dependency to requirement.
    """
    lst = [item for item in sorted(imported_by) if not item.startswith(name)]
    res = '%-15s # from: ' % name
    imps = ', '.join(lst)
    if len(imps) < WIDTH - 24:
        return res + imps
    return res + imps[:WIDTH - 24 - 3] + '...'


def pydeps2reqs(deps):
    """Convert a deps instance into requirements.
    """
    reqs = defaultdict(set)
    for k, v in list(deps.items()):
        # not a built-in
        p = v['path']
        if p and not p.startswith(sys.real_prefix):
            if p.startswith(sys.prefix) and 'site-packages' in p:
                if not p.endswith('.pyd'):
                    if '/win32/' in p.replace('\\', '/'):
                        reqs['win32'] |= set(v['imported_by'])
                    else:
                        name = k.split('.', 1)[0]
                        if name not in skiplist:
                            reqs[name] |= set(v['imported_by'])

    if '_dummy' in reqs:
        del reqs['_dummy']
    return '\n'.join(dep2req(name, reqs[name]) for name in sorted(reqs))


def main():
    """Cli entrypoint.
    """
    if len(sys.argv) == 2:
        fname = sys.argv[1]
        data = json.load(open(fname, 'rb'))
    else:
        data = json.loads(sys.stdin.read())
    print(pydeps2reqs(data))


if __name__ == "__main__":
    main()
