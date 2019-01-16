#!/usr/bin/env python
# identity.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0111

# Standard library imports
from __future__ import print_function
import argparse
import os
import re
import subprocess
import sys


###
# Functions
###
def _authors(fname):
    """Parse file and return user name and email of authors.

    Recognized author lines are of the form [NAME] <[EMAIL>, with an optional
    asterisk list marker before the name.
    """
    if not os.path.exists(fname):
        raise RuntimeError("File {} not found".format(fname))
    with open(fname, "r") as obj:
        lines = [_tostr(item.strip()) for item in obj.readlines()]
    regexp = re.compile(r"(?:\s*\*\s+)?(.*)\s+<(.*)>.*")
    for line in lines:
        match = regexp.match(line)
        if match:
            name, email = match.groups()
            yield name, email


def _git_cfg(token):
    """Return value of Git configuration field/token."""
    stdout, _ = subprocess.Popen(
        ["git", "config", token], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    return _tostr(stdout).strip()


def _tostr(line):  # pragma: no cover
    return (
        line
        if isinstance(line, str)
        else (line.decode() if sys.hexversion > 0x03000000 else line.encode())
    )


def check_identity(argv=None):
    """Script entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a", "--author-file", help="Author(s) file", nargs=1, required=True
    )
    parser.add_argument("files", nargs="*", help="Files in commit")
    args = parser.parse_args(argv)
    author_file = args.author_file[0]
    #
    git_name = _git_cfg("user.name")
    git_email = _git_cfg("user.email")
    retval = 0
    for name, email in _authors(author_file):
        if (git_name, git_email) == (name, email):
            break
    else:
        print(
            "Author {} <{}> not found in {} file".format(
                git_name, git_email, author_file
            )
        )
        retval = 1
    return retval


if __name__ == "__main__":
    sys.exit(check_identity())
