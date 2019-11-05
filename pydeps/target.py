# -*- coding: utf-8 -*-
"""
Abstracting the target for pydeps to work on.
"""
from __future__ import print_function
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import contextmanager


class Target(object):
    """The compilation target.
    """
    def __init__(self, path):
        self.calling_fname = path
        self.calling_dir = os.getcwd()
        self.exists = os.path.exists(path)
        if self.exists:
            self.path = os.path.realpath(path)
        else:  # pragma: nocover
            print("No such file or directory:", repr(path), file=sys.stderr)
            if os.path.exists(path + '.py'):
                print("..did you mean:", path + '.py', '?', file=sys.stderr)
            sys.exit(1)
        self.is_dir = os.path.isdir(self.path)
        self.is_module = self.is_dir and '__init__.py' in os.listdir(self.path)
        self.is_pysource = os.path.splitext(self.path)[1] in ('.py', '.pyc', '.pyo')
        self.fname = os.path.basename(self.path)
        if self.is_dir:
            self.dirname = self.fname
            self.modname = self.fname
        else:
            self.dirname = os.path.dirname(self.path)
            self.modname = os.path.splitext(self.fname)[0]

        self.workdir = os.path.realpath(tempfile.mkdtemp())
        self.syspath_dir = self.get_package_root()
        # split path such that syspath_dir + relpath == path
        self.relpath = self.path[len(self.syspath_dir):].lstrip(os.path.sep)
        if self.is_dir:
            self.modpath = self.relpath.replace(os.path.sep, '.')
        else:
            self.modpath = os.path.splitext(self.relpath)[0].replace(os.path.sep, '.')
        self.package_root = os.path.join(
            self.syspath_dir,
            self._path_parts(self.relpath)[0]
        )

    @contextmanager
    def chdir_work(self):
        try:
            os.chdir(self.workdir)
            sys.path.insert(0, self.syspath_dir)
            yield
        finally:
            os.chdir(self.calling_dir)
            if sys.path[0] == self.syspath_dir:
                sys.path = sys.path[1:]
            self.close()

    def get_package_root(self):
        for d in self.get_parents():
            if '__init__.py' not in os.listdir(d):
                return d

        raise Exception(
            "do you have an __init__.py file at the "
            "root of the drive..?")  # pragma: nocover

    def get_parents(self):
        def _parent_iter():
            parts = self._path_parts(self.path)
            for i in range(1, len(parts)):
                yield os.path.join(*parts[:-i])
        return list(_parent_iter())

    def _path_parts(self, pth):
        """Return a list of all directories in the path ``pth``.
        """
        res = re.split(r"[\\/]", pth)
        if res and os.path.splitdrive(res[0]) == (res[0], ''):
            res[0] += os.path.sep
        return res

    def __del__(self):
        self.close()

    def close(self):
        """Clean up after ourselves.
        """
        try:
            if hasattr(self, 'workdir'):
                shutil.rmtree(self.workdir)
        except OSError:
            pass

    def __repr__(self):  # pragma: nocover
        return json.dumps(
            {k: v for k, v in self.__dict__.items() if not k.startswith('_')},
            indent=4, sort_keys=True
        )
