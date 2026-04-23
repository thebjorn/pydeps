#!/usr/bin/env python
"""pydeps - Python module dependency visualization
"""
# pragma: nocover
import setuptools

version='3.0.5'


setuptools.setup(
    name='pydeps',
    version=version,
    packages=setuptools.find_packages(exclude=['tests*']),
    python_requires=">=3.10",
    install_requires=[
        'stdlib_list',
    ],
    long_description=open('README.rst', encoding='utf8').read(),
    entry_points={
        'console_scripts': [
            'pydeps = pydeps.pydeps:pydeps',
        ]
    },
    url='https://github.com/thebjorn/pydeps',
    license='BSD-2-Clause',
    author='bjorn',
    author_email='bp@datakortet.no',
    description='Display module dependencies',
    keywords='Python Module Dependency graphs',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
