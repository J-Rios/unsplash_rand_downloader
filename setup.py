#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script:
    setup.py
Description:
    Unsplash Random image downloader setup script for installation.
Author:
    Jose Miguel Rios Rubio
Creation date:
    22/01/2023
Last modified date:
    22/01/2023
Version:
    1.0.0
'''

###############################################################################
# Standard Libraries
###############################################################################

import os
import re
from setuptools import setup


###############################################################################
# Auxiliary Functions
###############################################################################

def get_long_description():
    '''Read and get module long description from README.md file.'''
    with open("README.md", encoding="utf8") as f:
        return f.read()


def get_variable(variable):
    '''Get a specific variable value from __init__.py file.'''
    with open(os.path.join("unsplash_rand_downloader", "__init__.py")) as f:
        return re.search(
            "{} = ['\"]([^'\"]+)['\"]".format(variable), f.read()
        ).group(1)  # type: ignore


###############################################################################
# Module Setup
###############################################################################

setup(
    name="unsplash_rand_downloader",
    description=get_variable("__description__"),
    long_description_content_type="text/markdown",
    long_description=get_long_description(),
    url=get_variable("__url__"),
    version=get_variable("__version__"),
    author=get_variable("__author__"),
    author_email=get_variable("__author_email__"),
    license=get_variable("__license__"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    keywords="unsplash, random, image",
    packages=[
        "unsplash_rand_downloader",
    ],
    include_package_data=True,
    install_requires=[
        "requests",
        "python-unsplash",
    ],
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
        "pytest-mock",
    ],
)
