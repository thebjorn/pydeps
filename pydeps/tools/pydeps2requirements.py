# -*- coding: utf-8 -*-
"""
Generate requirements.txt from pydeps output...

Usage::

    pydeps <packagename> --max-bacon=0 \
           --show-raw-deps --nodot \
           --noshow | python pydeps2requirements.py

"""
import json
import os
import site
import sys
from collections import defaultdict

from pydeps.package_names import find_package_names

WIDTH = 80

# packages that are difficult to eliminate but shouldn't ever be part
# of a package's requirements.
skiplist = {
    '_markerlib', 'pkg_resources'
}


def dep2req(name, package, imported_by):
    """Convert dependency to requirement.
    """
    lst = [item for item in sorted(imported_by) if not item.startswith(name)]
    res = '%-15s # from: ' % package
    imps = ', '.join(lst)
    if len(imps) < WIDTH - 24:
        return res + imps
    return res + imps[:WIDTH - 24 - 3] + '...'


_SITE_PACKAGE_DIRS = None


def site_packages():
    global _SITE_PACKAGE_DIRS
    if _SITE_PACKAGE_DIRS is None:
        site_package_dirs = [site.getusersitepackages()]
        site_package_dirs += site.getsitepackages()
        _SITE_PACKAGE_DIRS = []
        for pth in reversed(site_package_dirs):
            if os.path.isdir(pth):
                _SITE_PACKAGE_DIRS.append(pth)
    return _SITE_PACKAGE_DIRS


def is_site_package(p):
    for sp in site_packages():
        if p.startswith(sp):
            return True
    return False


def pydeps2reqs(deps):
    """Convert a deps instance into requirements.
    """
    reqs = defaultdict(set)
    baseprefix = sys.real_prefix if hasattr(sys, 'real_prefix') else sys.base_prefix
    pkgnames = find_package_names()

    for k, v in list(deps.items()):
        # not a built-in
        p = v['path']
        if p and not p.startswith(baseprefix):
            if is_site_package(p):
                if not p.endswith('.pyd'):
                    if '/win32/' in p.replace('\\', '/'):
                        reqs['win32'] |= set(v['imported_by'])
                    else:
                        name = k.split('.', 1)[0]
                        if name not in skiplist:
                            reqs[name] |= set(v['imported_by'])

    if '_dummy' in reqs:
        del reqs['_dummy']
    return '\n'.join(dep2req(name, pkgnames[name], reqs[name]) for name in sorted(reqs))


def main():
    """Cli entrypoint.
    """
    if len(sys.argv) == 2:
        fname = sys.argv[1]
        with open(fname, 'rb') as fp:
            data = json.load(fp)
    else:
        data = json.loads(sys.stdin.read())
    print(pydeps2reqs(data))


if __name__ == "__main__":
    main()
