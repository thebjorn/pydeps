# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import site


def find_package_names():
    site_package_dirs = site.getsitepackages()
    site_package_dirs.append(site.getusersitepackages())
    # initialize with well-known packages that don't seem to have a top_level.txt
    res = {
        'yaml': 'PyYAML',
        'Crypto': 'pycrypto',
    }
    for site_packages in reversed(site_package_dirs):
        if not os.path.isdir(site_packages):
            continue
        for pth in os.listdir(site_packages):
            if not pth.endswith('.dist-info'):
                continue
            pkgname = pth.split('-', 1)[0].replace('_', '-')
            top_level_fname = os.path.join(site_packages, pth, 'top_level.txt')
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
