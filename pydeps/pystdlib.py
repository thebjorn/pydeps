# -*- coding: utf-8 -*-

import sys
import stdlib_list


def pystdlib():
    """Return a set of all module-names in the Python standard library.
    """
    curver = '.'.join(str(x) for x in sys.version_info[:2])
    return (set(stdlib_list.stdlib_list(curver)) | {
        '_LWPCookieJar', '_MozillaCookieJar', '_abcoll', 'email._parseaddr',
        'email.base64mime', 'email.feedparser', 'email.quoprimime',
        'encodings', 'genericpath', 'ntpath', 'nturl2path', 'os2emxpath',
        'posixpath', 'sre_compile', 'sre_parse', 'unittest.case',
        'unittest.loader', 'unittest.main', 'unittest.result',
        'unittest.runner', 'unittest.signals', 'unittest.suite',
        'unittest.util', '_threading_local', 'sre_constants', 'strop',
        'repr', 'opcode', 'nt', 'encodings.aliases',
        '_bisect', '_codecs', '_collections', '_functools', '_hashlib',
        '_heapq', '_io', '_locale', '_LWPCookieJar', '_md5',
        '_MozillaCookieJar', '_random', '_sha', '_sha256', '_sha512',
        '_socket', '_sre', '_ssl', '_struct', '_subprocess',
        '_threading_local', '_warnings', '_weakref', '_weakrefset',
        '_winreg'
    }) - {'__main__'}
