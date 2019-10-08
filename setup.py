#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0',
                'flask>=1.1.1',
                'peewee>=3.11.2',
                'fabric>=2.5.0',
                'asyncio>=3.4.3',
                'gunicorn>=19.9.0',
                'watchdog>=0.9.0',
                'hachiko>=0.2.0',
                'aiohttp>=3.6.1',
                'namesgenerator>=0.3',
                'python-daemon>=2.2.3',
                'protobuf>=3.10.0',
                'purerpc>=0.5.2'
                ]

setup_requirements = [ ]

test_requirements = [ 'hypothesis>=4.38.0', ]

setup(
    author="Justin Payne",
    author_email='justin.payne@fda.hhs.gov',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="To help you manage your pores",
    entry_points={
        'console_scripts': [
            'prfr=porerefiner.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='porerefiner',
    name='porerefiner',
    packages=find_packages(include=['porerefiner', 'porerefiner.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/crashfrog/porerefiner',
    version='0.1.0',
    zip_safe=False,
)
