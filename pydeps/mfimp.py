"""
Python's modulefinder._find_module has a bug that breaks a number of popular
packages.

This is a copy of the standard lib's imp._find_module, extended to also
recognize PEP 420 implicit namespace packages (directories without an
__init__.py).

This is vendorized/copied here to prevent the warning error that the regular
imp module causes.
"""

from _imp import is_builtin, is_frozen
from importlib import machinery
import sys
import os
import tokenize


PY_SOURCE = 1
PY_COMPILED = 2
C_EXTENSION = 3
PKG_DIRECTORY = 5
C_BUILTIN = 6
PY_FROZEN = 7
NAMESPACE_PACKAGE = 10


def _get_suffixes():
    extensions = [(s, 'rb', C_EXTENSION) for s in machinery.EXTENSION_SUFFIXES]
    source = [(s, 'r', PY_SOURCE) for s in machinery.SOURCE_SUFFIXES]
    bytecode = [(s, 'rb', PY_COMPILED) for s in machinery.BYTECODE_SUFFIXES]

    return extensions + source + bytecode


def find_module(name, path=None):
    if not isinstance(name, str):
        raise TypeError("'name' must be a str, not {}".format(type(name)))
    elif not isinstance(path, (type(None), list)):
        # Backwards-compatibility
        raise RuntimeError("'path' must be None or a list, "
                           "not {}".format(type(path)))

    if path is None:
        if is_builtin(name):
            return None, None, ('', '', C_BUILTIN)
        elif is_frozen(name):
            return None, None, ('', '', PY_FROZEN)
        else:
            path = sys.path

    namespace_directory = None
    for entry in path:
        package_directory = os.path.join(entry, name)
        for suffix in ['.py', machinery.BYTECODE_SUFFIXES[0]]:
            package_file_name = '__init__' + suffix
            file_path = os.path.join(package_directory, package_file_name)
            if os.path.isfile(file_path):
                return None, package_directory, ('', '', PKG_DIRECTORY)
        for suffix, mode, type_ in _get_suffixes():
            file_name = name + suffix
            file_path = os.path.join(entry, file_name)
            if os.path.isfile(file_path):
                break
        else:
            # PEP 420: a directory without __init__.py is a namespace
            # package. Remember the first match and fall back to it only if
            # no regular module or package is found in any later entry.
            if namespace_directory is None and os.path.isdir(package_directory):
                namespace_directory = package_directory
            continue
        break  # Break out of outer loop when breaking out of inner loop.
    else:
        if namespace_directory is not None:
            return None, namespace_directory, ('', '', NAMESPACE_PACKAGE)
        raise ImportError('No module named {!r}'.format(name), name=name)

    encoding = None
    if 'b' not in mode:
        with open(file_path, 'rb') as file:
            encoding = tokenize.detect_encoding(file.readline)[0]
    file = open(file_path, mode, encoding=encoding)
    return file, file_path, (suffix, mode, type_)
