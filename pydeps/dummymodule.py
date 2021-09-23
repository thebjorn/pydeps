# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import textwrap
import logging

from . import cli

log = logging.getLogger(__name__)


def is_module(directory):
    """A directory is a module if it contains an ``__init__.py`` file.
    """
    return os.path.isdir(directory) and '__init__.py' in os.listdir(directory)


def is_pysource(fname):
    """A file name is a python source file iff it ends with '.py' and doesn't
       start with a dot.
    """
    return not fname.startswith('.') and fname.endswith('.py')


def fname2modname(fname, package_root):
    subpath = os.path.splitext(fname)[0][len(package_root):]
    modname = subpath.lstrip(os.path.sep).replace(os.path.sep, '.')
    return modname


def python_sources_below(directory, package=True):
    for root, dirs, files in os.walk(directory):
        if package and '__init__.py' not in files:
            continue
        dotdirs = [d for d in dirs if d.startswith('.')]
        for d in dotdirs:
            dirs.remove(d)
        if 'migrations' in dirs:
            dirs.remove('migrations')
        for fname in files:
            if is_pysource(fname):  # and fname not in args['exclude']:
                if fname == '__init__.py':
                    yield os.path.abspath(root)
                else:
                    yield os.path.abspath(os.path.join(root, fname))


class DummyModule(object):
    """We create a file that imports the module to be investigated.
    """
    def __init__(self, target, **args):
        self._legal_mnames = {}
        self.target = target
        self.fname = '_dummy_' + target.modpath.replace('.', '_') + '.py'
        self.absname = os.path.join(target.workdir, self.fname)
        log.debug("dummy-filename: %r (%s)", self.fname, self.absname)

        if target.is_module:
            cli.verbose(1, "target is a PACKAGE")
            with open(self.fname, 'w') as fp:
                for fname in python_sources_below(target.package_root):
                    modname = fname2modname(fname, target.syspath_dir)
                    self.print_import(fp, modname)

        elif target.is_dir:
            # FIXME?: not sure what the intended semantics was here, as it is
            #         this will almost certainly not do the right thing...
            cli.verbose(1, "target is a DIRECTORY")
            with open(self.fname, 'w') as fp:
                for fname in os.listdir(target.dirname):
                    if is_pysource(fname):
                        self.print_import(fp, fname2modname(fname, ''))

        else:
            assert target.is_pysource
            cli.verbose(1, "target is a FILE")
            with open(self.fname, 'w') as fp:
                self.print_import(fp, target.modpath)

    def text(self):
        """Return the content of the dummy module.
        """
        with open(self.fname) as fp:
            return fp.read()

    def legal_module_name(self, name):
        """Legal module names are dotted strings where each part
           is a valid Python identifier.
           (and not a keyword, and support unicode identifiers in
           Python3, ..)
        """
        if name in self._legal_mnames:
            return self._legal_mnames[name]

        for part in name.split('.'):
            try:
                exec("%s = 42" % part, {}, {})
            except:  # pragma: nocover  # noqa
                self._legal_mnames[name] = False
                return False
        self._legal_mnames[name] = True
        return True

    def print_header(self, fp):  # pragma: nocover
        # we're not executing the file in fp, so really not necessary to
        # catch import errors
        print(textwrap.dedent("""
            import sys
            import traceback
        """), file=fp)

    def print_import(self, fp, module):
        if not self.legal_module_name(module):
            log.warning("SKIPPING ILLEGAL MODULE_NAME: %s", module)
            return

        mparts = module.rsplit('.', 1)
        # we're not executing the file in fp, so really not necessary to
        # catch import errors
        if len(mparts) == 1:
            print(textwrap.dedent("""\
                import {module}
            """).format(module=module), file=fp)
        else:
            print(textwrap.dedent("""\
                from {prefix} import {mname}
            """).format(prefix=mparts[0], mname=mparts[1]), file=fp)
        # if len(mparts) == 1:
        #     print(textwrap.dedent("""\
        #         import {module}
        #     """).format(module=module))
        # else:
        #     print(textwrap.dedent("""\
        #         from {prefix} import {mname}
        #     """).format(prefix=mparts[0], mname=mparts[1]))
