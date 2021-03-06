#-*-coding:utf-8-*-
"""
@package bapp.tests.doc.test_examples
@brief See bapp.tests.doc for more information

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import sys

import bapp
from butility.tests import (TestCaseBase,
                            with_rw_directory)

import bcmd



# ==============================================================================
## \name TestTypes
# ------------------------------------------------------------------------------
# Types that derive from the type to be tested
## \{

## [ExampleCommand]
class ExampleCommand(bcmd.CommandBase):
    """A command with verbosity argument"""
    __slots__ = ()
    
    name = 'example'
    version = '1.0'
    description = 'a simple example'
    
    def setup_argparser(self, parser):
        """Add our arguments"""
        parser.add_argument('-v', 
                            action='count', 
                            default=0, 
                            dest='verbosity',
                            help='set the verbosity level - more v characters increase the level')
        return self
        
    def execute(self, args, remaining_args):
        """Be verbose or not"""
        if args.verbosity > 0:
            print 'executing example'
        if args.verbosity > 1:
            print 'Its my first time ...'
        if args.verbosity > 2:
            print 'and it feels great'
        
        return 0
        
# end class ExampleCommand
        
## [ExampleCommand] 
        
## [ExampleCommandWithSubcommands]
class MasterCommand(bcmd.CommandBase):
    """Allows for subcommands"""
    
    name = 'master'
    version = '1.5'
    description = 'a simple example command with subcommands support'
    
    subcommands_title = 'Modes'
    subcommands_help = 'All modes we support - type "example <mode> --help" for mode-specific help'
    
    # execute() is implemented by our base to handle subcommands automatically - we don't do anything

# end class MasterCommand

class ExampleSubCommand(ExampleCommand, bcmd.SubCommandBase, bapp.plugin_type()):
    """Shows how to use an existing command as mode of a master command.
    @note we make ourselves a plugin to allow the CommandBase implementation to find our command.
    This can also be overridden if no plugin system is required, using the 
    bcmd.CommandBase._find_compatible_subcommands() method"""
    
    # this associates us with the main command
    main_command_name = MasterCommand.name
    
    # And this is it - otherwise you would have to implement a SubCommand as any other command
    
# end class ExampleSubCommand
    
## [ExampleCommandWithSubcommands]


## -- End TestTypes -- \}
