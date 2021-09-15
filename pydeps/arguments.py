from __future__ import print_function, unicode_literals
import warnings
import json
import argparse
from .pycompat import configparser

try:
    unicode     # noqa

    def is_string(v):
        return isinstance(v, (str, unicode))    # noqa
except NameError:
    def is_string(v):
        return isinstance(v, str)


DEFAULT_NONE = '____'


def boolval(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return bool(v)
    if is_string(v):
        v = v.lower()
        if v in {'j', 'y', 'ja', 'yes', '1', 'true'}:
            return True
        if v in {'n', 'nei', 'no', '0', 'false'}:
            return False
    raise ValueError("Don't know how to convert %r to bool" % v)


def listval(v):
    if is_string(v):
        return [x for x in v.split() if x.strip()]
    if isinstance(v, (list, tuple)):
        return v
    raise ValueError("Don't know how to convert %r to list" % v)


def identity(v):
    return v


typefns = {
    'BOOL': boolval,
    'INT': int,
    'LIST': listval
}


class Argument(object):
    def __init__(self, *flags, **args):
        self._args = args
        self._flags = flags
        # self.__dict__.update(args)

    def __json__(self):
        return self.__dict__

    def typename(self):
        if 'kind' in self._args:
            return self._args['kind']
        if self._args.get('action') in {'store_true', 'store_false'}:
            return 'BOOL'
        tp = self._args.get('type')
        if tp is not None:
            return tp.__name__.upper()
        v = self._args.get('default')
        if v is None:
            return DEFAULT_NONE
        return v.__class__.__name__.upper()

    def argname(self):
        if 'dest' in self._args:
            return self._args['dest']
        return self._flags[-1].lstrip('-').replace('-', '_')

    def default(self):
        if 'default' in self._args:
            return self._args['default']
        if self._args.get('action') == 'store_true':
            return False
        if self._args.get('action') == 'store_false':
            return True
        return '___'

    def add_to_parser(self, parser):
        args = self._args
        args.pop('default', None)  # remove default value
        args.pop('kind', None)     # remove our attributes
        if args.get('action') in {'store_true', 'store_false'}:
            args['default'] = None
        parser.add_argument(*self._flags, **args)


class Namespace(object):
    def __init__(self, ns):
        self.ns = ns

    def __repr__(self):
        return json.dumps(vars(self.ns), indent=4, sort_keys=True)

    def items(self):
        return list(dict(vars(self.ns)).items())

    def __getitem__(self, key):
        return getattr(self.ns, key)

    def __setitem__(self, key, val):
        setattr(self.ns, key, val)

    def __delitem__(self, key):
        delattr(self.ns, key)

    def __getattr__(self, key):
        return getattr(self.ns, key)


class Arguments(object):
    def __init__(self, config_files=None, debug=False, *posargs, **kwargs):
        # passthrough to argparse
        self.posargs = posargs
        self.kwargs = kwargs
        # print("CONFIG_FILES:", config_files)

        self.debug = debug
        self.arglist = []
        self.args = {}
        self.config_files = config_files
        self.argtypes = {}
        self.defaults = {}

    def parse_args(self, argv):
        config = []
        if self.config_files:
            conf = configparser.SafeConfigParser()
            conf.read(self.config_files)
            try:
                config = conf.items("pydeps")
            except (configparser.NoOptionError, configparser.NoSectionError):
                warnings.warn(' '.join("""
                    Couldn't find a [pydeps] section in your config files
                    %r -- or it was empty
                """.split()) % (self.config_files,))
        p = argparse.ArgumentParser(*self.posargs, **self.kwargs)
        for arg in self.arglist:
            arg.add_to_parser(p)
        args = Namespace(p.parse_args(argv))

        for key, val in config:
            if key not in self.args:
                warnings.warn("Your .pydeps file contained %s = %s which doesn't match any argument" % (key, val))
                continue
            argval = args[key]
            confval = val
            typeval = self.argtypes[key]
            typfn = typefns[typeval]
            if argval is None:
                args[key] = typfn(confval)

        for key, val in args.items():
            if val in (None, DEFAULT_NONE):
                default = self.defaults.get(key)
                if default == DEFAULT_NONE:
                    default = None
                args[key] = default

        del args['config']
        return args.ns

    def add(self, *flags, **kwargs):
        arg = Argument(*flags, **kwargs)
        self.arglist.append(arg)
        argname = arg.argname()
        self.args[argname] = arg
        self.argtypes[argname] = arg.typename()
        self.defaults[argname] = arg.default()

    def __repr__(self):
        return json.dumps(dict(
            types=self.argtypes,
            defaults=self.defaults,
        ), indent=4, sort_keys=True)
