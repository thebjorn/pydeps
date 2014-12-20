# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os
import shutil
import tempfile
import yaml


class FilemakerBase(object):  # pragma: nocover
    """Override marked methods to do something useful.  Base class serves as
       a dry-run step generator.
    """

    def __init__(self, root, fdef):
        self.fdef = fdef
        self.goto_root(root)
        self._makefiles(fdef)

    def goto_root(self, dirname):
        """override
        """
        print "pushd", dirname

    def makedir(self, dirname, content):
        """override, but call self.make_list(content)
        """
        print "mkdir " + dirname
        print "pushd " + dirname
        self.make_list(content)
        print "popd"

    def make_file(self, filename, content):
        """override
        """
        print "create file: %s %r" % (filename, content)

    def make_empty_file(self, fname):
        """override
        """
        print "touch", fname

    def _make_empty_file(self, fname):
        if fname != 'empty':
            self.make_empty_file(fname)

    def make_list(self, lst):
        for item in lst:
            self._makefiles(item)

    def _makefiles(self, f):
        if isinstance(f, dict):
            for k, v in f.items():
                if isinstance(v, list):
                    self.makedir(dirname=k, content=v)
                elif isinstance(v, basestring):
                    self.make_file(filename=k, content=v)
                else:  # pragma: nocover
                    raise ValueError("Unexpected:", k, v)
        elif isinstance(f, basestring):
            self._make_empty_file(f)
        elif isinstance(f, list):
            self.make_list(f)
        else:  # pragma: nocover
            raise ValueError("Unknown type:", f)


class Filemaker(FilemakerBase):
    def goto_root(self, dirname):
        os.chdir(dirname)

    def makedir(self, dirname, content):
        cwd = os.getcwd()
        os.mkdir(dirname)
        os.chdir(dirname)
        self.make_list(content)
        os.chdir(cwd)

    def make_file(self, filename, content):
        open(filename, 'w').write(content)

    def make_empty_file(self, fname):
        open(fname, 'w').close()


@contextmanager
def create_files(filedef, cleanup=True):
    fdef = yaml.load(filedef)
    cwd = os.getcwd()
    tmpdir = tempfile.mkdtemp()
    try:
        Filemaker(tmpdir, fdef)
        if not cleanup:
            print "TMPDIR =", tmpdir
        yield tmpdir
    finally:
        os.chdir(cwd)
        if cleanup:
            shutil.rmtree(tmpdir, ignore_errors=True)
