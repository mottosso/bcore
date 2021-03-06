#-*-coding:utf-8-*-
"""
@package bprocess.utility
@brief A collection of utilities to ease the work of controller and delegate

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['controller_schema', 'process_schema', 'package_schema', 'python_package_schema',
           'package_meta_data_schema', 'package_manager_schema']

import logging
import sys
import re

from bkvstore import (KeyValueStoreSchema,
                      AnyKey,
                      StringList,
                      PathList,
                      KVPathList,
                      KVPath,
                      KVStringFormatter)
from .interfaces import IProcessControllerDelegate
from butility import (Version,
                      Path )

log = logging.getLogger('bprocess.schema')

# ==============================================================================
## @name Utilities
# ------------------------------------------------------------------------------
## @{

class NamedServiceProcessControllerDelegate(object):
    """Utility type to create a delegate as a service from the given name.
    We use it as dynamic constructor"""
    __slots__ = ('_delegate_name')
    
    def __init__(self, delegate_name = None):
        """Fill our instance"""
        self._delegate_name = delegate_name
        
    def instance(self, context_stack, *args, **kwargs):
        """@return a new instance of a type which matches our stored name, or None if our name was None
        @param context_stack the context to use when trying to find the named type
        @param args
        @param kwargs given to new instance"""
        if not self._delegate_name:
            return
        # end handle value unset
        
        delegates = context_stack.new_instances(IProcessControllerDelegate, 
                        maycreate = lambda cls, instances: not instances and cls.__name__ == self._delegate_name,
                        args = args, kwargs = kwargs)
        if not delegates:
            raise AssertionError("Delegate named '%s' could not be found in service registry" % self._delegate_name)
        # handle delegate instantiation
        
        return delegates[0]

    def name(self):
        """@return the name of the delegate we should instantiate"""
        return self._delegate_name
         

# end class NamedServiceProcessControllerDelegate


class IgnoreCaseRegex(object):
  """A type to handle conversions from and to regular expressions.
  It will handle invalid ones such that it logs the error, and retains one that never matches.

  Instance of this type also act as a proxy for their regex.
  """
  __slots__ = ('regex') # a precompiled and valid regular expression object

  flags = re.IGNORECASE
  never_match = '(?!)'
  re_never_match = re.compile(never_match)

  def __init__(self, regex=never_match):
      """Initialize ourselves with a regex, which is compiled right away"""
      try:
          self.regex = re.compile(regex, flags=self.flags)
      except re.error, err:
          self.log.error("regex compilation failed: %s", err)
          # This regex is supposed to never match anything
          self.regex = self.re_never_match
      # end handle regex conversion

  def __getattr__(self, name):
      """Proxy for regex"""
      return getattr(self.regex, name)

# end class Regex

## -- End Utilities -- @}


process_schema = KeyValueStoreSchema('process', { 
                                                    # kvstore id of the program to run, usually the basename of the executable
                                                    'id' : str,
                                                    # Full path to the executable we were supposed to run
                                                    'executable' : Path,
                                                    # directory at which bcore can be imported from. This is the
                                                    # location at which the process controller code exists
                                                    'core_tree' : Path,
                                                    # The executable of the python interpreter we are currently
                                                    # running in, sys.executable
                                                    'python_executable' : Path,
                                                    # The arguments the process was started with.
                                                    # May contain bootstrapper arguments as well
                                                    'raw_arguments' : StringList
                                                }
                                    )

# Importantly, we only want this type within the kvstore resolve, not for ourselves !
for key in ('executable', 'core_tree'):
    KVStringFormatter.set_key_type(key, KVPath)
# end for each key to set

# NOTE: just because without these, the process engine is not usable, we keep them as default
# for use in the inherit_regex
_inherit_evars = ['PATH',         # Actually to allow other wrapper scripts to work, i.e. maya
                  'HOME',         # used by some software to find local configuration
                           ]
if sys.platform == 'win32':
    _inherit_evars.extend(('USERNAME',     # required to have user information (simple)
                           'SystemRoot'    # required for most APIs to work !
                            ))
else:
    _inherit_evars.extend(('XAUTHORITY',   # just here as a precaution 
                           'DISPLAY',      # To allow GUIs
                           'USER',         # Some programs need it, like 3de
                         ))
# end handle platforms

# A schema to configure the package manager system on a global level. That way, it is more flexible, 
# helping to reduce the requirement for custom delegates
package_manager_schema = KeyValueStoreSchema('package-manager', 
                                                    {'include' : PathList,
                                                     'environment' : {
                                                        'variables' : {
                                                          'inherit' : StringList(_inherit_evars),
                                                          'regex' : {
                                                             # all matches are case-insensitive
                                                             'is_path'            : IgnoreCaseRegex('.*path'),
                                                             'path_is_appendable' : IgnoreCaseRegex('')
                                                             }
                                                          } # end variables
                                                       }# end environment
                                                    })

package_schema = KeyValueStoreSchema(AnyKey,            # Path to the root of the package. All relative paths will be 
                                                        # made absolute with the first valid root path
                                                        { 'trees' : KVPathList,
                                                         # absolute or relative path to the executable    
                                                          'executable' : Path,
                                                          # Path to the current working directory of the process
                                                          # This will not affect the current working dir set for 
                                                          # setting up the configuration
                                                          'cwd' : Path,
                                                          # We are explicit about our delegate type, so this needs to be overridden
                                                          'delegate' : NamedServiceProcessControllerDelegate('ProcessControllerDelegate'),
                                                          # A list of packages that we depend on, and whose 
                                                          # configuration we will need
                                                          'requires' : StringList,
                                                          # A list of packages not to consider in our requirements
                                                          # only used when building the process environment
                                                          'ignore' : StringList,
                                                          # An alias to the package which provides the executable of our program.
                                                          # The delegate may be overridden here, and all 
                                                          # all environment variables
                                                          'alias' : str,
                                                          # The python configuration only at boot time (using the bootstrapper)
                                                          'boot' : {
                                                            # The sys.paths to set in order to allow imports
                                                            'python_paths' : PathList,
                                                            # A list of modules which are to be imported
                                                            'import' : StringList,
                                                            # A list of paths to directories and files from which all python files should be loaded non-recursively
                                                            # May also be a python file to be executed
                                                            'plugin_paths' : PathList,
                                                          },
                                                          'version' : Version(),
                                                          # Allows to specify additional configuration 
                                                          # that we have to pull in. It affects the bootstrapper
                                                          # as well as the launched process
                                                          'include': PathList,
                                                          'arguments' : {
                                                              # Arguments to append
                                                              'append' : StringList,
                                                              # arguments to prepend
                                                              'prepend' : StringList,
                                                              # if True, we will substitute environment variables
                                                              # The first encountered True value will enable it
                                                              'resolve' : False
                                                          },
                                                          # tractor specific information
                                                          'environment' : {
                                                              # If True, the entire environment will be inherited. 
                                                              # Otherwise the process will build its environment from 
                                                              # scratch.
                                                              'inherit' : False,
                                                              # if True, environment variables specified here
                                                              # will be substituted automatically
                                                              'resolve' : False,
                                                              'linker_search_paths' : PathList,
                                                              'executable_search_paths' : PathList,
                                                              # Environment Variables we are to set
                                                              'variables' : {
                                                                AnyKey : StringList
                                                              }
                                                           },
                                                        # a list of keys into the package actions
                                                        # Dictionary. It is accessed using a variable schema
                                                        # depending on the type of action.
                                                        # Specified using type.name
                                                        'actions' : StringList
                                                        }
                                                    )

KVStringFormatter.set_key_type_by_schema(package_schema, ('trees', 'version'))

## This doesn't need to be a schema, its used as building block to make one
python_package_schema = {
                               'requires' : package_schema.requires,
                               'version' : package_schema.version,
                               'trees': package_schema.trees,
                               'python' : {
                                    # A list of modules that is to be imported
                                    'import' : StringList,
                                    # A list of python files to be executed. This will also make their code
                                    # in available, or register plugins
                                    # May contain directories, from which all python files will be loaded
                                    # non-recursively
                                    'plugin_paths' : PathList
                               }
                         }


## see python_package_schema
package_meta_data_schema = {
                                'requires' : package_schema.requires,
                                'name' : str,
                                'url' : str,
                                'description' : str,
                                'version': package_schema.version
                           }

controller_schema = KeyValueStoreSchema('packages', { package_schema.key() : package_schema })

