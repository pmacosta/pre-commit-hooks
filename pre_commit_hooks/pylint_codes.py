#!/usr/bin/env python
# pylint_codes.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0103,C0111,R0912

# Standard library imports
from __future__ import print_function
import argparse
import os
import re
import sys

###
# Global variables
###
IS_PY3 = sys.hexversion > 0x03000000


###
# Functions
###
def _check_pylint_codes(fname):
    """Check that there are no repeated Pylint codes per file."""
    # pylint: disable=R0914
    rec = re.compile
    soline = rec(r"(^\s*)#\s*pylint\s*:\s*disable\s*=\s*([\w|\s|,]+)\s*")
    # Regular expression to get a Pylint disable directive but only
    # if it is not in a string
    template = r"#\s*pylint:\s*disable\s*=\s*([\w|\s|\s*,\s*]+)"
    quoted_eol = rec(r'(.*)(\'|")\s*' + template + r"\s*\2\s*")
    eol = rec(r"(.*)\s*" + template + r"\s*")
    file_tokens = []
    for input_line in _read_file(fname):
        line_match = soline.match(input_line)
        quoted_eol_match = quoted_eol.match(
            input_line.replace("\\n", "\n").replace("\\r", "\r")
        )
        eol_match = eol.match(input_line)
        if eol_match and (not quoted_eol_match) and (not line_match):
            return True
        if line_match:
            unsorted_tokens = line_match.groups()[1].rstrip().split(",")
            sorted_tokens = sorted(unsorted_tokens)
            if any([item in file_tokens for item in sorted_tokens]) or (
                unsorted_tokens != sorted_tokens
            ):
                return True
            file_tokens.extend(sorted_tokens)
    return False


def _read_file(fname):
    """Return file lines as strings."""
    with open(fname) as fobj:
        for line in fobj:
            yield _tostr(line).rstrip()


def _tostr(obj):  # pragma: no cover
    """Convert to string if necessary."""
    return obj if isinstance(obj, str) else (obj.decode() if IS_PY3 else obj.encode())


def _valid_file(value):
    """Check that a file exists and returned it converted to absolute path."""
    if not os.path.isabs(value):
        value = os.path.abspath(os.path.join(os.getcwd(), value))
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError("File {0} does not exist".format(value))
    return value


def check_pylint_codes(argv=None):
    """Run aspell and report line number in which misspelled words are."""
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=_valid_file)
    cli_args = parser.parse_args(argv)
    fnames = cli_args.files
    retval = 0
    for fname in fnames:
        if _check_pylint_codes(fname):
            retval = 1
            print("    " + fname)
    return retval


if __name__ == "__main__":
    sys.exit(check_pylint_codes(sys.argv[1:]))
