
import setuptools
from distutils.core import setup

setup(
    name='pydeps',
    version='0.9.2',
    packages=['pydeps'],
    install_requires=[
        'enum34'
    ],
    entry_points={
        'console_scripts': [
            'py2dep = pydeps.py2depgraph:py2depgraph',
            'dep2dot = pydeps.depgraph2dot:depgraph2dot',
            'pydeps = pydeps.pydeps:pydeps',
        ]
    },
    url='https://github.com/thebjorn/pydeps',
    license='BSD',
    author='bjorn',
    author_email='bp@datakortet.no',
    description='Display module dependencies'
)
