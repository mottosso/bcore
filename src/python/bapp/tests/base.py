#-*-coding:utf-8-*-
"""
@package bapp.tests.base
@brief most fundamental types

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""

import logging

import bapp
from butility.tests import TestCaseBase
from butility import (Path,
                      wraps,
                      partial)

log = logging.getLogger('bapp.tests')


# ==============================================================================
## @name Decorators
# ------------------------------------------------------------------------------
## @{

def preserve_application(fun):
    """A wrapper which preserves whichever value was in bapp.Application.main during
    the test-case"""
    @wraps(fun)
    def wrapper(*args, **kwargs):
        prev = bapp.Application.main
        try:
            return fun(*args, **kwargs)
        finally:
            bapp.Application.main = prev
        # end reset Application
    # end wrapper
    return wrapper


def with_application(fun=None, **dkwargs):
    """similar to preserve_application(), but will create a new application object that will 
    be discarded once the decorated function completes.
    It's useful if there is ApplictionSettingsClient code that tries to access the central information database
    @param dkwargs are given to bapp.Application.new()
    @note you can use the custom parameter from_file=__file__ to append the given file to the settings_trees of
    the new application.
    It will also make sure the stack receives the initial types, which were gathered by the default context
    while there was no application"""
    if fun is None:
        p = partial(with_application, **dkwargs)
        p.__module__ = p.__name__ = str()
        return p
    # end handle custom arguments

    @wraps(fun)
    def wrapper(*args, **kwargs):
        from_file = dkwargs.pop('from_file', None)
        prev = bapp.Application.main
        if from_file:
            settings_trees = dkwargs.setdefault('settings_trees', list())
            settings_trees.append(Path(from_file).dirname())
        # end handle arguments
        # never load user settings
        dkwargs['user_settings'] = False
        app = bapp.Application.new(**dkwargs)

        # Make sure the default context is inserted, if it doesn't have it
        has_default_ctx = False
        for ctx in app.context().stack():
            has_default_ctx = ctx.name() == bapp.Application.PRE_APPLICATION_CONTEXT_NAME
            if has_default_ctx:
                break
            # end context found
        # end find default context if possible

        if not has_default_ctx:
            # We have incredible knowledge about this implementation, and probably shouldn't use it !
            # We know there is a default 
            app.context().stack().insert(1, bapp.Application.Plugin.default_stack)
        # end 

        try:
            return fun(*args, **kwargs)
        finally:
            # we don't have to do anything with the default context, it will just remain in the origin
            bapp.Application.main = prev
        # end assure original application is put back
    # end wrapper
    return wrapper
    

## -- End Decorators -- @}


# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class TestCoreCaseBase(TestCaseBase):
    __slots__ = ()

    fixture_root = Path(__file__).dirname()

# end class TestCaseBase

## -- End Types -- @}





