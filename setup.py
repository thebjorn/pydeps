
import setuptools
#from setuptools import setup
from distutils.core import setup

setup(
    name='pydeps',
    version='1.1.0',
    packages=['pydeps'],
    install_requires=[
        'enum34'
    ],
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            #'py2dep = pydeps.py2depgraph:py2depgraph',
            #'dep2dot = pydeps.depgraph2dot:depgraph2dot',
            'pydeps = pydeps.pydeps:pydeps',
        ]
    },
    url='https://github.com/thebjorn/pydeps',
    license='BSD',
    author='bjorn',
    author_email='bp@datakortet.no',
    description='Display module dependencies',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
