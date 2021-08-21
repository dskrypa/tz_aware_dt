#!/usr/bin/env python

from pathlib import Path
from setuptools import setup

project_root = Path(__file__).resolve().parent

with project_root.joinpath('readme.rst').open('r', encoding='utf-8') as f:
    long_description = f.read()

about = {}
with project_root.joinpath('tz_aware_dt', '__version__.py').open('r', encoding='utf-8') as f:
    exec(f.read(), about)


setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=long_description,
    url=about['__url__'],
    project_urls={'Source': 'https://github.com/dskrypa/tz_aware_dt'},
    packages=['tz_aware_dt'],
    license=about['__license__'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='~=3.6',
    install_requires=['python-dateutil', 'tzlocal>=3.0'],
    extras_require={'dateparser': ['dateparser'], 'dev': ['pre-commit', 'ipython']},
)
