#!/usr/bin/env python
# pydocstyle_wrapper.py
# Copyright (c) 2019 Pablo Acosta-Serafini
# See LICENSE for details
# pylint: disable=C0111,W0613

# Standard library imports
import re
import sys
# PyPI imports
from pydocstyle.cli import main


###
# Functions
###
def check_pydocstyle(argv=None):
    """Script entry point."""
    return main()


if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(check_pydocstyle(sys.argv))
