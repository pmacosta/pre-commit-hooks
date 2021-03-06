#!/usr/bin/env python
# header.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0103,C0111,R0912,R0914

# Standard library imports
from __future__ import print_function
import argparse
import datetime
from fnmatch import fnmatch
import os
import re
import sys

###
# Global variables
###
IS_PY3 = sys.hexversion > 0x03000000


###
# Functions (common with plugin)
###
def _check_header(fname, streamer, comment="#", header_ref=""):
    """Check that all files have header line and copyright notice."""
    # pylint: disable=W0702
    header_ref = header_ref.strip() or _find_header_ref(fname)
    if not header_ref:
        print(
            "Reference header file .headerrc not found, skipping header check",
            file=sys.stderr,
        )
        return []
    fullname = os.path.basename(os.path.abspath(fname))
    basename = os.path.basename(os.path.abspath(fname))
    current_year = datetime.datetime.now().year
    header_lines = []
    for line in _read_file(header_ref):
        line = line.format(
            comment=comment,
            fullname=fullname,
            basename=basename,
            current_year=current_year,
        )
        header_lines.append(re.compile("^" + line + "$"))
    linenos = []
    with streamer(fname) as stream:
        for (num, line), regexp in zip(_content_lines(stream, comment), header_lines):
            if not regexp.match(line):
                linenos.append(num)
    return linenos


def _content_lines(stream, comment="#"):
    """Return non-empty lines of a package."""
    shebang_line_regexp = re.compile(r"^#!.*[ \\/](bash|python)$")
    sl_mod_docstring = re.compile("('''|\"\"\").*('''|\"\"\")")
    encoding_dribble = "\xef\xbb\xbf"
    shebang_line = False
    in_mod_docstring = False
    mod_string_done = False
    cregexp = re.compile(r"^{0} -\*- coding: utf-8 -\*-\s*".format(comment))
    for num, line in enumerate(stream):
        line = _tostr(line).rstrip()
        if (not num) and line.startswith(encoding_dribble):
            line = line[len(encoding_dribble) :]
        # Skip shebang line
        if (not num) and shebang_line_regexp.match(line):
            shebang_line = True
            continue
        # Skip file encoding line
        if (num == int(shebang_line)) and cregexp.match(line):
            continue
        # Skip single-line module docstring
        if (not num) and sl_mod_docstring.match(line):
            continue
        if (not num) and (not mod_string_done) and line.startswith('"""'):
            in_mod_docstring = True
            continue
        if in_mod_docstring and line.endswith('"""'):
            in_mod_docstring = False
            mod_string_done = True
            continue
        if (not mod_string_done) and in_mod_docstring:
            continue
        yield num + 1, line


def _find_header_ref(fname):
    """Find .headerrc file."""
    curr_dir = ""
    next_dir = os.path.dirname(os.path.abspath(fname))
    while next_dir != curr_dir:
        curr_dir = next_dir
        rcfile = os.path.join(curr_dir, ".headerrc")
        if os.path.exists(rcfile):
            return rcfile
        next_dir = os.path.dirname(curr_dir)
    return ""


def _read_file(fname):
    """Return file lines as strings."""
    with open(fname) as fobj:
        for line in fobj:
            yield _tostr(line).strip()


def _tostr(obj):  # pragma: no cover
    """Convert to string if necessary."""
    return obj if isinstance(obj, str) else (obj.decode() if IS_PY3 else obj.encode())


class StreamFile(object):
    # pylint: disable=R0903
    """Stream class."""

    def __init__(self, lint_file):  # noqa
        self.fname = lint_file

    def __enter__(self):  # noqa
        with open(self.fname, "r") as fobj:
            for line in fobj:
                yield line

    def __exit__(self, exc_type, exc_value, exc_tb):  # noqa
        return not exc_type is not None


###
# Hook-specific functions
###
def _make_abspath(value):
    """Homogenize files to have absolute paths."""
    value = value.strip()
    if not os.path.isabs(value):
        value = os.path.abspath(os.path.join(os.getcwd(), value))
    return value


def _valid_file(value):
    """Check that a file exists and returned it converted to absolute path."""
    value = _make_abspath(value)
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError("File {0} does not exist".format(value))
    return value


def check_header(argv=None):
    """Run aspell and report line number in which misspelled words are."""
    argv = sys.argv[1:] if argv is None else argv
    # Apparently the personal dictionary cannot be a relative path
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exclude", nargs=1, type=_valid_file, required=False)
    parser.add_argument("files", nargs="*", type=_valid_file)
    cli_args = parser.parse_args(argv)
    ###
    fnames = cli_args.files
    if cli_args.exclude:
        patterns = [_make_abspath(item) for item in _read_file(cli_args.exclude[0])]
        exclude_filter = lambda x: not any(fnmatch(x, pattern) for pattern in patterns)
        fnames = filter(exclude_filter, fnames)
    ###
    fdict = {".py": "#", ".rst": "..", ".ini": "#", ".sh": "#", ".cfg": "#"}
    retval = 0
    for fname in fnames:
        _, ext = os.path.splitext(fname)
        if (ext in fdict) and _check_header(fname, StreamFile, fdict[ext]):
            retval = 1
            print("    " + fname.strip())
    return retval


if __name__ == "__main__":
    sys.exit(check_header(sys.argv[1:]))
