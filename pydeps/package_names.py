# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import site


def _find_top_level_file(site_pkg_dir, pth):
    if pth.endswith('.dist-info') or pth.endswith('.egg-info'):
        top_level_fname = os.path.join(site_pkg_dir, pth, 'top_level.txt')
    elif pth.endswith('.egg'):
        top_level_fname = os.path.join(site_pkg_dir, pth, 'EGG-INFO', 'top_level.txt')
    else:
        top_level_fname = None
    return top_level_fname


def _extract_pkg_name(pth):
    name = pth.rsplit('.', 1)[0]
    name_no_version = name.split('-', 1)[0]
    return name_no_version.replace('_', '-')


def find_package_names():
    # initialize with well-known packages that don't seem to have a top_level.txt
    res = {
        'yaml': 'PyYAML',
        'Crypto': 'pycrypto',
    }
    site_package_dirs = [site.getusersitepackages()]
    site_package_dirs += site.getsitepackages()

    for site_packages in reversed(site_package_dirs):
        if not os.path.isdir(site_packages):
            continue

        for pth in os.listdir(site_packages):
            top_level_fname = _find_top_level_file(site_packages, pth)
            if top_level_fname is None:
                continue

            pkgname = _extract_pkg_name(pth)

            if not os.path.exists(top_level_fname):
                if pkgname not in res.values():
                    print("ERR:", pth, 'has not top_level.txt')
                continue

            with open(top_level_fname) as fp:
                modnames = fp.read().split()

            for modname in modnames:
                modname = modname.replace('/', '.')
                if modname.startswith(r'win32\lib'):
                    modname = modname.rsplit('\\')[1]
                res[modname] = pkgname

    return res


if __name__ == "__main__":
    import json
    print(json.dumps(find_package_names(), indent=4, sort_keys=True))
