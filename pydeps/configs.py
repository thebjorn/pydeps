    
from io import StringIO
import json
import warnings
import logging

log = logging.getLogger(__name__)

# from devtools import debug


HAVE_TOML = False
try:
    import tomllib as toml
    HAVE_TOML = True
except ImportError:
    try:
        import tomlkit as toml
        HAVE_TOML = True
    except ImportError:
        try:
            import toml
            HAVE_TOML = True
        except ImportError:
            pass


def is_string(v):
    return isinstance(v, str)
    

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
    'LIST': listval,
    'STR': str,
}


def load_toml(filename):
    if not HAVE_TOML:
        return {}
    try:
        with open(filename) as fp:
            res = toml.loads(fp.read())
        return res['tool']['pydeps']
    except Exception as e:
        log.debug("Couldn't load toml file %s: %s", filename, e)
        return {}


def load_json(filename):
    try:
        with open(filename) as fp:
            res = json.loads(fp.read())
        return res['pydeps']
    except (json.JSONDecodeError, KeyError):
        return {}


def load_yaml(filename):
    try:
        import yaml
        from yaml import Loader
        with open(filename) as fp:
            res = yaml.load(fp.read(), Loader=Loader)
        return res['pydeps']
    except (yaml.YAMLError, KeyError, ImportError):
        return {}


def load_ini(filename):
    import configparser
    conf = configparser.ConfigParser()
    conf.read(filename)
    try:
        config = conf.items("pydeps")
        return dict(config)
    except (configparser.NoOptionError, configparser.NoSectionError):
        warnings.warn(' '.join("""
            Couldn't find a [pydeps] section in your config files
            %r -- or it was empty
        """.split()) % filename)
    return {}


def load_config(filename):
    if filename.endswith('.toml'):
        return load_toml(filename)
    if filename.endswith('.json'):
        return load_json(filename)
    if filename.endswith('.yaml'):
        return load_yaml(filename)
    raise ValueError("Unknown config file type: %s" % filename)


# this class is generated from pydeps.arguments.Arguments.write_default_config()
class Config(object):
    #: turn on all the show and verbose options (mainly for debugging pydeps
    #: itself)
    debug = False

    #: specify config file
    config = None

    #: disable processing of config files
    no_config = False

    #: print pydeps version
    version = False

    #:  set log-level to one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
    log = None

    #: tries to automatically find the name of the current package.
    find_package = False

    #: filename
    fname = None

    #: be more verbose (-vv, -vvv for more verbosity)
    verbose = 0

    #: write output to 'file'
    output = None

    #: output format (svg|png)
    format = 'svg'

    #: program to use to display the graph (png or svg file depending on the T
    #: parameter)
    display = None

    #: don't call external program to display graph
    no_show = False

    #: show output of dependency analysis
    show_deps = False

    #: show output of dependency analysis before removing skips
    show_raw_deps = False

    #: write output of dependency analysis to 'file'
    deps_out = None

    #: show output of dot conversion
    show_dot = False

    #: write dot code to 'file'
    dot_out = None

    #: skip dot conversion
    no_dot = False

    #: don't create .svg/.png file, implies --no-show (-t/-o will be ignored)
    no_output = False

    #: show only import cycles
    show_cycles = False

    #: set the ModuleFinder.debug flag to this value
    debug_mf = 0

    #: exclude sources or sinks with degree greater than noise-level
    noise_level = 200

    #: exclude nodes that are more than n hops away (default=2, 0 -> infinite)
    max_bacon = 2

    #: coalesce deep modules to at most n levels
    max_module_depth = 0

    #: include python std lib modules
    pylib = False

    #: include python all std lib modules (incl. C modules)
    pylib_all = False

    #: include modules that are not installed (or can't be found on sys.path)
    include_missing = False

    #: input files to skip (e.g. `foo.*`), multiple file names can be provided
    exclude = []

    #: same as --exclude, except requires the full match. `-xx foo.bar` will
    #: exclude foo.bar, but not foo.bar.blob
    exclude_exact = []

    #: only include modules that start with MODULE_PATH
    only = []

    #: create list of direct external dependencies
    externals = False

    #: draw arrows to (instead of from) imported modules
    reverse = False

    #: set the direction of the graph, legal values are TB (default, imported
    #: modules above importing modules), BT (opposite direction of TB),
    #: LR (left-to-right), and RL (right-to-left)
    rankdir = 'TB'

    #: draw external dependencies as separate clusters
    cluster = False

    #: the minimum number of nodes a dependency must have before being clustered
    #: (default=0)
    min_cluster_size = 0

    #: the maximum number of nodes a dependency can have before the cluster is
    #: collapsed to a single node (default=0)
    max_cluster_size = 0

    #: draw target module as a cluster
    keep_target_cluster = False

    #: collapse target module (--keep-target-cluster will be ignored)
    collapse_target_cluster = False

    #: remove PREFIX from the displayed name of the nodes
    rmprefix = []

    #: starting value for hue from 0 (red/default) to 360.
    start_color = 0

    def __init__(self, **kwargs):
        for key in dir(self.__class__):
            if not key.startswith('_'):
                val = getattr(self.__class__, key)
                if not callable(val):
                    setattr(self, key, val)
        self.__dict__.update(kwargs)

    def __eq__(self, other):
        res = True
        for (lkey, lval), (rkey, fval) in zip(iter(self), iter(other)):
            if lkey != rkey:
                print(f"key mismatch: {lkey} != {rkey}")
                res = False
            if lval != fval:
                print(f"val mismatch {lkey}: {lval} != {fval}")
                res = False
        return res

    def set_field(self, field, value):
        if field == 'fname':
            self.fname = identity(value)
        if field == 'verbose':
            self.verbose = int(value)
        if field == 'output':
            self.output = identity(value)
        if field == 'format':
            self.format = str(value)
        if field == 'display':
            self.display = identity(value)
        if field == 'no_show':
            self.no_show = boolval(value)
        if field == 'show_deps':
            self.show_deps = boolval(value)
        if field == 'show_raw_deps':
            self.show_raw_deps = boolval(value)
        if field == 'deps_out':
            self.deps_out = identity(value)
        if field == 'show_dot':
            self.show_dot = boolval(value)
        if field == 'dot_out':
            self.dot_out = identity(value)
        if field == 'no_dot':
            self.no_dot = boolval(value)
        if field == 'no_output':
            self.no_output = boolval(value)
        if field == 'show_cycles':
            self.show_cycles = boolval(value)
        if field == 'debug_mf':
            self.debug_mf = int(value)
        if field == 'noise_level':
            self.noise_level = int(value)
        if field == 'max_bacon':
            self.max_bacon = int(value)
        if field == 'max_module_depth':
            self.max_module_depth = int(value)
        if field == 'pylib':
            self.pylib = boolval(value)
        if field == 'pylib_all':
            self.pylib_all = boolval(value)
        if field == 'include_missing':
            self.include_missing = boolval(value)
        if field == 'exclude':
            self.exclude = listval(value)
        if field == 'exclude_exact':
            self.exclude_exact = listval(value)
        if field == 'only':
            self.only = listval(value)
        if field == 'externals':
            self.externals = boolval(value)
        if field == 'reverse':
            self.reverse = boolval(value)
        if field == 'rankdir':
            self.rankdir = str(value)
        if field == 'cluster':
            self.cluster = boolval(value)
        if field == 'min_cluster_size':
            self.min_cluster_size = int(value)
        if field == 'max_cluster_size':
            self.max_cluster_size = int(value)
        if field == 'keep_target_cluster':
            self.keep_target_cluster = boolval(value)
        if field == 'collapse_target_cluster':
            self.collapse_target_cluster = boolval(value)
        if field == 'rmprefix':
            self.rmprefix = listval(value)
        if field == 'start_color':
            self.start_color = int(value)

    def __iter__(self):
        return iter(self.__dict__.items())

    def __getattr__(self, name):
        return self.__dict__[name]

    def update(self, data):
        if set(data.keys()) - set(self.__dict__.keys()):
            warnings.warn("Unknown config keys: %s" % (set(data.keys()) - set(self.__dict__.keys())))
        for k, v in data.items():
            if k in self.__dict__:
                self.set_field(k, v)

    def write_ini(self):
        import configparser
        cfg = configparser.ConfigParser()
        cfg['pydeps'] = {k: str(v) for k, v in self}
        with StringIO() as fp:
            cfg.write(fp)
            return fp.getvalue()

    def write_toml(self):
        import tomlkit
        return tomlkit.dumps({
            'tools.pydeps': {k: v for k, v in self if v is not None}
        })

    def write_json(self):
        data = {'pydeps': self.__dict__}
        return json.dumps(data, indent=4)
    
    def write_yaml(self):
        import yaml
        data = {'pydeps': self.__dict__}
        return yaml.dump(data, default_flow_style=False)

    @classmethod
    def load(cls, fnames):
        """Load config from file.
        """
        conf = cls()

        for fname in fnames:
            ftype = filetype(fname)

            if ftype == 'toml':
                conf.update(load_toml(fname))
            if ftype == 'json':
                conf.update(load_json(fname))
            if ftype == 'yaml':
                conf.update(load_yaml(fname))
            if ftype == 'ini':
                conf.update(load_ini(fname))

        return conf


def filetype(fname):
    if fname.endswith('.toml'):
        return 'toml'
    elif fname.endswith('.json'):
        return 'json'
    elif fname.endswith('.yaml'):
        return 'yaml'
    elif fname.endswith('.yml'):
        return 'yaml'
    elif fname.endswith('.ini'):
        return 'ini'
    else:
        return 'ini'
