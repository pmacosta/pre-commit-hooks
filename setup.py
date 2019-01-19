# setup.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0111

# Standard library imports
from setuptools import find_packages
from setuptools import setup


###
# Functions
###
setup(
    name="pre_commit_hooks",
    description="Various pre-commit framework hooks.",
    url="https://github.com/pmacosta/pre-commit-hooks",
    version="1.0.0",
    author="Pablo Acosta-Serafini",
    author_email="pmasdev@gmail.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    packages=find_packages(exclude=("tests*", "testing*")),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "identity = pre_commit_hooks.identity:check_identity",
            "pydocstyle_wrapper = pre_commit_hooks.pydocstyle_wrapper:check_pydocstyle",
            "spelling = pre_commit_hooks.spelling:check_spelling",
        ]
    },
)
