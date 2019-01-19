#!/usr/bin/env python
# spelling.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0103,C0111,R0912,R0914

# Standard library imports
from __future__ import print_function
import argparse
import collections
from fnmatch import fnmatch
import io
import os
import re
from subprocess import Popen, PIPE
import sys

# Literal copy from [...]/site-packages/pip/_vendor/compat.py
try:
    from shutil import which
except ImportError:  # pragma: no cover
    # Implementation from Python 3.3
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """Mimic CLI which function, copied from Python 3.3 implementation."""
        # pylint: disable=C0113,W0622
        # Check that a given file can be accessed with the correct mode.
        # Additionally check that `file` is not a directory, as on Windows
        # directories pass the os.access check.
        def _access_check(fn, mode):
            return os.path.exists(fn) and os.access(fn, mode) and not os.path.isdir(fn)

        # If we're given a path with a directory part, look it up directly rather
        # than referring to PATH directories. This includes checking relative to the
        # current directory, e.g. ./script
        if os.path.dirname(cmd):
            if _access_check(cmd, mode):
                return cmd
            return None

        if path is None:
            path = os.environ.get("PATH", os.defpath)
        if not path:
            return None
        path = path.split(os.pathsep)

        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            if not os.curdir in path:
                path.insert(0, os.curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path extensions.
            # This will allow us to short circuit when given "python.exe".
            # If it does match, only test that one, otherwise we have to try
            # others.
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if not normdir in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None


###
# Global variables
###
IS_PY3 = sys.hexversion > 0x03000000


###
# Functions
###
def _grep(fname, words):
    """Return line numbers in which words appear in a file."""
    # pylint: disable=W0631
    pat = "(.*[^a-zA-Z]|^){}([^a-zA-Z].*|$)"
    regexps = zip(words, [re.compile(pat.format(word)) for word in words])
    ldict = collections.defaultdict(list)
    for num, line in enumerate(_read_file(fname)):
        for word in [word for word, regexp in regexps if regexp.match(line)]:
            ldict[word].append(str(num + 1))
    return ldict


def _read_file(fname):
    """Return file lines as strings."""
    with open(fname) as fobj:
        for line in fobj:
            yield _tostr(line).strip()


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


def check_spelling(argv=None):
    """Run aspell and report line number in which misspelled words are."""
    if not which("aspell"):
        print("aspell not found, skipping spell checking")
        return 0
    argv = sys.argv[1:] if argv is None else argv
    # Apparently the personal dictionary cannot be a relative path
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--personal", nargs=1, type=_valid_file, required=False)
    parser.add_argument("-e", "--exclude", nargs=1, type=_valid_file, required=False)
    parser.add_argument("files", nargs="*", type=_valid_file)
    cli_args, cmd_args = parser.parse_known_args(argv)
    ###
    if cli_args.personal:
        cmd_args.append("--personal={}".format(cli_args.personal[0]))
    fnames = cli_args.files
    if cli_args.exclude:
        patterns = list(_read_file(cli_args.exclude[0]))
        exclude_filter = lambda x: not any(fnmatch(x, pattern) for pattern in patterns)
        fnames = filter(exclude_filter, fnames)
    ###
    cmd = ["aspell"] + cmd_args + ["list"]
    retval = 0
    for fname in fnames:
        with io.open(fname) as fobj:
            obj = Popen(cmd, stdin=fobj, stdout=PIPE, stderr=PIPE)
            stdout = _tostr(obj.communicate()[0]).split(os.linesep)
        words = sorted(list(set([line for line in stdout if line.strip()])))
        if words:
            retval = 1
            ldict = _grep(fname, words)
            print(fname)
            for word, lines in [(word, ldict[word]) for word in words]:
                plural = "s" if len(lines) > 1 else ""
                print("    {}: line{} {}".format(word, plural, ", ".join(lines)))
    return retval


if __name__ == "__main__":
    sys.exit(check_spelling(sys.argv[1:]))
