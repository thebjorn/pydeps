#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pydeps - Python module dependency visualization
"""
# pragma: nocover
import io
import sys

import setuptools
from distutils.core import setup
from setuptools.command.test import test as TestCommand

version = "1.9.3"


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

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


setup(
    name="pydeps",
    version=version,
    packages=["pydeps"],
    install_requires=[
        'enum34; python_version < "3.4"',
        "stdlib-list>=0.6.0",
        "future >= 0.18.2",
    ],
    long_description=io.open("README.rst", encoding="utf8").read(),
    entry_points={"console_scripts": ["pydeps = pydeps.pydeps:pydeps"]},
    url="https://github.com/thebjorn/pydeps",
    cmdclass={"test": PyTest},
    license="BSD",
    author="bjorn",
    author_email="bp@datakortet.no",
    description="Display module dependencies",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    extras_require={
        "dev": [
            "PyYAML>=3.12",
            "cov-core==1.15.0",
            "coverage==4.5.1",
            "pytest==3.7.1",
            "pytest-cov==2.5.1",
            "Sphinx>=1.7.6",
        ]
    },
)
