#-*-coding:utf-8-*-
"""
@package bapp.tests
Main test package for all bapp code.

Provides core functionality which will be used by all test cases in one way or another.

Imports bapp.tests

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""

# Import all core features into the main package
import sys
from .base import *

import logging
from butility import init_ipython_terminal


def _initialize():
    """Add some utilities"""
    # be sure we can easily start ipython from an interpreter
    import __builtin__
    setattr(__builtin__, 'ipy', init_ipython_terminal)
    
    # Set debug logging for test cases
    logging.root.setLevel(logging.DEBUG)
    
#end _initialize


_initialize()
    

