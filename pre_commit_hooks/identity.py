#!/usr/bin/env python
# identity.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0111

# Standard library imports
from __future__ import print_function
import os
import re
import subprocess
import sys


###
# Functions
###
def _git_cfg(token):
    """Return value of Git configuration field/token."""
    stdout, _ = subprocess.Popen(
        ["git", "config", token], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    return stdout.strip()


def _authors(fname):
    """Parse file and return user name and email of authors.

    Recognized author lines are of the form [NAME] <[EMAIL>, with an optional
    asterisk list marker before the name.
    """
    if not os.path.exists(fname):
        raise RuntimeError("File {} not found".format(fname))
    with open(fname, "r") as obj:
        lines = [item.strip() for item in obj.readlines()]
    regexp = re.compile(r"(?:\s*\*\s+)?(.*)\s+<(.*)>.*")
    for line in lines:
        match = regexp.match(line)
        if match:
            name, email = match.groups()
            yield name, email


def main(args):
    """Script entry point."""
    if len(args) > 1:
        raise RuntimeError('Too many input arguments')
    fname = os.path.abspath(args[0])
    git_name = _git_cfg("user.name")
    git_email = _git_cfg("user.email")
    ret_code = 0
    for name, email in _authors(fname):
        if (git_name, git_email) == (name, email):
            break
    else:
        print("Author {} <{}> not found in {} file".format(git_name, git_email, fname))
        ret_code = 1
    sys.exit(ret_code)


if __name__ == "__main__":
    main(sys.argv[1:])
