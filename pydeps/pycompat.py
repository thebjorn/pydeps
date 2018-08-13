# -*- coding: utf-8 -*-
"""
Compatibility imports between py2/py3
"""
# pragma: nocover
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
