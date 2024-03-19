from __future__ import print_function, unicode_literals
from io import StringIO
import textwrap
import json
import argparse
# from devtools import debug
from .configs import Config, typefns, identity

DEFAULT_NONE = '____'


class Argument(object):
    def __init__(self, *flags, **args):
        if 'choices' in args and args['choices'] is None:
            del args['choices']
        if 'container' in args:
            del args['container']
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
    
    def typefn(self):
        return typefns.get(self.typename(), identity)

    def pytype(self):
        argname = self.argname()
        if argname == 'fname':
            return 'str'
        if 'choices' in self._args:
            return 'Literal[%s]' % ', '.join(repr(x) for x in self._args['choices'])
        if 'type' in self._args:
            res = self._args['type']
        elif self._args.get('action') in {'store_true', 'store_false'}:
            res = bool
        elif self._args.get('kind', 'unknown') is None:
            return 'None'
        elif self._args.get('kind', '').startswith("FNAME"):
            res = str
        else:
            res = self._args.get('default').__class__
        if res is None:
            return 'None'
        return res.__name__

    def argname(self):
        if 'dest' in self._args:
            return self._args['dest']
        return self._flags[0].lstrip('-').replace('-', '_')
        # return self._flags[-1].lstrip('-').replace('-', '_')
    
    def help(self):
        if 'help' in self._args:
            return self._args['help']
        return ''

    def default(self):
        if 'default' in self._args:
            return self._args['default']
        if self._args.get('action') == 'store_true':
            return False
        if self._args.get('action') == 'store_false':
            return True
        return DEFAULT_NONE

    def add_to_parser(self, parser):
        args = self._args
        args.pop('default', None)  # remove default value
        args.pop('kind', None)     # remove our attributes
        if args.get('action') in {'store_true', 'store_false'}:
            args['default'] = None
        # debug("ADD_TO_PARSER:", self._flags, args)
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
    def __init__(self, config_files=None, debug=False, *posargs, parents=None, **kwargs):
        if config_files is None:
            config_files = []
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
        self.parents = parents

    def load_config_files(self):
        for filename in self.config_files:
            if filename == '.pydeps' or filename.endswith('.pydeps'):
                self.load_pydeps_config(filename)

    def write_default_config(self):
        """Utility function to create .configs.Config

           # XXX: a more general utility to create configs from argparse
           #      would be nice...
        """
        fp = StringIO()
        # fp = sys.stdout
        print("class Config(object):", file=fp)

        arglist = self.arglist

        if self.parents:
            parent_actions = []
            for parent in self.parents:
                for action in parent._actions:
                    # if isinstance(action, argparse._StoreAction):
                    parent_actions.append(Argument(
                        *action.option_strings, **action.__dict__
                    ))
            arglist = parent_actions + arglist

        for arg in arglist:
            debug(arg._args)
            
            default = arg.default()
            if default == DEFAULT_NONE:
                default = None
            elif isinstance(default, str):
                default = repr(default)

            help = textwrap.wrap(arg.help(), 80 - 7)  # 7 = len("    #: ")
            for helpline in help:
                print("", file=fp)
                print("    #: {help}".format(help=helpline), end="", file=fp)
            print("", file=fp)

            typename = arg.pytype()
            if typename == 'list' and default is None:
                typename = 'Optional[List[str]]'
            elif default is None:
                typename = f'Optional[{typename}]'
            elif default == [] and typename == 'list':
                typename = 'List[str]'
            # add py3 type annotations
            # print(f"    {arg.argname()}: {typename} = {default}", file=fp)
            
            # witout type annotations
            print("    {argname} = {default}".format(argname=arg.argname(), default=default), file=fp)

        print("", file=fp)
        print("    def set_field(self, field, value):", file=fp)
        for arg in self.arglist:
            print("        if field == '{argname}':".format(argname=arg.argname()), file=fp)
            print("            self.{argname} = {typefn}(value)".format(argname=arg.argname(), typefn=arg.typefn().__name__), file=fp)
        print("", file=fp)
        # debug(res)
        res = fp.getvalue()
        print(res)
        return res

    def parse_args(self, argv):
        self.kwargs['parents'] = self.parents
        p = argparse.ArgumentParser(*self.posargs, **self.kwargs)
        for arg in self.arglist:
            arg.add_to_parser(p)
        args = Namespace(p.parse_args(argv))

        config = Config.load(self.config_files)
        config.update({k: v for k, v in args.items() if v is not None})

        # print('---- yaml ---------------')
        # print(config.write_yaml())
        # print('---- json ---------------')
        # print(config.write_json())
        # print('---- ini ---------------')
        # print(config.write_ini())
        # print('---- toml ---------------')
        # print(config.write_toml())
        # print('-------------------')

        return config

    def add(self, *flags, **kwargs):
        # debug(flags, kwargs)
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
