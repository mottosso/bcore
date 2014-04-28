#-*-coding:utf-8-*-
"""
@package bprocess.utility
@brief A collection of utilities to ease the work of controller and delegate

@copyright 2013 Sebastian Thiel
"""
__all__ = ['controller_schema', 'process_schema', 'package_schema', 'python_package_schema',
           'package_meta_data_schema', 'package_manager_schema']

import logging

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

## -- End Utilities -- @}


process_schema = KeyValueStoreSchema('process', { 
                                                    # kvstore id of the program to run, usually the basename of the executable
                                                    'id' : str,
                                                    # Full path to the executable we were supposed to run
                                                    'executable' : Path,
                                                    # directory at which bcore can be imported from. This is the
                                                    # location at which the process controller code exists
                                                    'core_tree' : Path,
                                                    # The arguments the process was started with.
                                                    # May contain bootstrapper arguments as well
                                                    'raw_arguments' : StringList
                                                }
                                    )

# Importantly, we only want this type within the kvstore resolve, not for ourselves !
for key in ('executable', 'core_tree'):
    KVStringFormatter.set_key_type(key, KVPath)
# end for each key to set

_config_schema = dict( trees = PathList,
                       # Files are loaded after trees, and may thus override
                       # whatever came in from them
                       files =  PathList )

# A schema to configure the package manager system on a global level. That way, it is more flexible, 
# helping to reduce the requirement for custom delegates
package_manager_schema = KeyValueStoreSchema('package-manager', {'configuration' : _config_schema})

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
                                                          'exclude' : StringList,
                                                          # An alias to the package which provides the executable of our program.
                                                          # The delegate may be overridden here, and all 
                                                          # all environment variables
                                                          'alias' : str,
                                                          # If True, the entire environment will be inherited. Otherwise the process will build its environment from scratch.
                                                          'inherit_environment' : False,
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
                                                          'configuration': _config_schema,
                                                          'arguments' : {
                                                              # Arguments to append
                                                              'append' : StringList,
                                                              # arguments to prepend
                                                              'prepend' : StringList
                                                          },
                                                          # tractor specific information
                                                          'environment' : {
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

