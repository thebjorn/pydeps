#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pydeps - Python module dependency visualization
"""
# pragma: nocover
import io
import sys

import setuptools
from setuptools.command.test import test as TestCommand

version='1.10.17'


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setuptools.setup(
    name='pydeps',
    version=version,
    packages=['pydeps'],
    install_requires=[
        'enum34; python_version < "3.4"',
        'stdlib_list',
    ],
    long_description=io.open('README.rst', encoding='utf8').read(),
    entry_points={
        'console_scripts': [
            'pydeps = pydeps.pydeps:pydeps',
        ]
    },
    url='https://github.com/thebjorn/pydeps',
    cmdclass={'test': PyTest},
    license='BSD',
    author='bjorn',
    author_email='bp@datakortet.no',
    description='Display module dependencies',
    keywords='Python Module Dependency graphs',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
