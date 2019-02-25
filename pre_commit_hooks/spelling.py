#!/usr/bin/env python
# spelling.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0103,C0111,E1129,R0205,R0912,R0914,R1718,W0640,W1113

# Standard library imports
from __future__ import print_function
import argparse
import collections
from fnmatch import fnmatch
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import types

# PyPI imports
import decorator

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
@decorator.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


class TmpFile(object):
    """
    Use a temporary file within context.

    From pmisc package
    """

    def __init__(self, fpointer=None, *args, **kwargs):  # noqa
        if (
            fpointer
            and (not isinstance(fpointer, types.FunctionType))
            and (not isinstance(fpointer, types.LambdaType))
        ):
            raise RuntimeError("Argument `fpointer` is not valid")
        self._fname = None
        self._fpointer = fpointer
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):  # noqa
        fdesc, fname = tempfile.mkstemp()
        # fdesc is an OS-level file descriptor, see problems if this
        # is not properly closed in this post:
        # https://www.logilab.org/blogentry/17873
        os.close(fdesc)
        if platform.system().lower() == "windows":  # pragma: no cover
            fname = fname.replace(os.sep, "/")
        self._fname = fname
        if self._fpointer:
            with open(self._fname, "w") as fobj:
                self._fpointer(fobj, *self._args, **self._kwargs)
        return self._fname

    def __exit__(self, exc_type, exc_value, exc_tb):  # noqa
        with ignored(OSError):
            os.remove(self._fname)
        return not exc_type is not None


def _cleanup_word(word):
    """Strip out leading trailing spaces, quotes and double quotes."""
    if not word.strip():
        return ""
    regexp = re.compile(r"(?:[^a-zA-Z]*|^)*([a-zA-Z]+)(?:[^a-zA-Z]*|$)*")
    match = regexp.match(word)
    if match:
        return match.groups()[0].strip()
    return ""


def _grep(fname, words):
    """Return line numbers in which words appear in a file."""
    # pylint: disable=W0631
    pat = "(.*[^a-zA-Z]|^){}([^a-zA-Z].*|$)"
    regexps = [(word, re.compile(pat.format(word))) for word in words]
    ldict = collections.defaultdict(list)
    for num, line in enumerate(_read_file(fname)):
        for word in [word for word, regexp in regexps if regexp.match(line)]:
            ldict[word].append(str(num + 1))
    return ldict


def _make_abspath(value):
    """Homogenize files to have absolute paths."""
    value = value.strip()
    if not os.path.isabs(value):
        value = os.path.abspath(os.path.join(os.getcwd(), value))
    return value


def _read_file(fname):
    """Return file lines as strings."""
    with open(fname) as fobj:
        for line in fobj:
            yield _tostr(line).strip()


def _shcmd(cmd, timeout=15):
    """Safely execute shell command."""
    delay = 1.0
    obj = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sys.hexversion < 0x03000000:
        while (obj.poll() is None) and (timeout > 0):
            time.sleep(delay)
            timeout -= delay
        if not timeout:
            obj.kill()
        stdout, stderr = obj.communicate()
    else:
        try:
            stdout, stderr = obj.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            obj.kill()
            stdout, stderr = obj.communicate()
    if obj.returncode:
        print("COMMAND: " + (" ".join(cmd)))
        print("STDOUT:" + os.linesep + _tostr(stdout))
        print("STDERR:" + os.linesep + _tostr(stderr))
        raise RuntimeError("hunspell command could not be executed successfully")
    stdout = _tostr(stdout).split(os.linesep)
    stderr = _tostr(stderr).split(os.linesep)
    return stdout


def _tostr(obj):  # pragma: no cover
    """Convert to string if necessary."""
    return obj if isinstance(obj, str) else (obj.decode() if IS_PY3 else obj.encode())


def _valid_file(value):
    """Check that a file exists and returned it converted to absolute path."""
    value = _make_abspath(value)
    if not os.path.exists(value):
        raise argparse.ArgumentTypeError("File {0} does not exist".format(value))
    return value


def check_spelling(argv=None):
    """Run aspell and report line number in which misspelled words are."""
    if not which("hunspell"):
        print("hunspell not found, skipping spell checking")
        return 0
    argv = sys.argv[1:] if argv is None else argv
    # Apparently the personal dictionary cannot be a relative path
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", nargs=1, required=False)
    parser.add_argument("-i", nargs=1, required=False)
    parser.add_argument("-p", nargs=1, type=_valid_file, required=False)
    parser.add_argument("-P", nargs=1, required=False)
    parser.add_argument("-e", "--exclude", nargs=1, type=_valid_file, required=False)
    parser.add_argument("files", nargs="*", type=_valid_file)
    cli_args, cmd_args = parser.parse_known_args(argv)
    ###
    fnames = cli_args.files
    if cli_args.exclude:
        patterns = [_make_abspath(item) for item in _read_file(cli_args.exclude[0])]
        exclude_filter = lambda x: not any(fnmatch(x, pattern) for pattern in patterns)
        fnames = filter(exclude_filter, fnames)
    ###
    cmd_args += ["-d", cli_args.d[0]] if cli_args.d else []
    cmd_args += ["-i", cli_args.i[0]] if cli_args.i else []
    cmd_args += ["-p", cli_args.p[0]] if cli_args.p else []
    cmd_args += ["-P", cli_args.P[0]] if cli_args.P else []
    retval = 0
    base_cmd = ["hunspell"] + cmd_args + ["-l"]
    for fname in fnames:
        # First pass
        stdout = _shcmd(base_cmd + [fname])
        words = [_cleanup_word(word) for word in stdout if word.strip()]
        words = sorted(list(set([word for word in words if word.strip()])))
        # Second pass
        func = lambda x: x.write(os.linesep.join(words))
        with TmpFile(func) as temp_fname:
            stdout = _shcmd(base_cmd + [temp_fname])
        words = sorted(list(set([word.strip() for word in stdout if word.strip()])))
        #
        header_printed = False
        if words:
            retval = 1
            ldict = _grep(fname, words)
            if not header_printed:
                print("Base command: " + (" ".join(base_cmd)))
                header_printed = True
            print(fname)
            for word, lines in [(word, ldict[word]) for word in words]:
                plural = "s" if len(lines) > 1 else ""
                print("    {}: line{} {}".format(word, plural, ", ".join(lines)))
    return retval


if __name__ == "__main__":
    sys.exit(check_spelling(sys.argv[1:]))
