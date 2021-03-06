#-*-coding:utf-8-*-
"""
@package bapp.tests.cmd.test_base
@brief tests for bcmd.base

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

import bapp
from bapp.tests import with_application
from butility.tests import TestCaseBase

# Test * import
from bcmd import *


class SimpleCommand(CommandBase):
    """Just to run the code"""
    __slots__ = ()
    
    name = 'simple'
    version = '1.0.2-beta'
    log_id = name
    description = 'The first command'
    
    def setup_argparser(self, parser):
        parser.add_argument('-x', type=int, required=True)
        return self
        
    def execute(self, args, remaining):
        assert not remaining
        assert isinstance(args.x, int)
        return 0

# end class SimpleCommand


class MainCommand(CommandBase):
    """A command providing subcommands"""
    __slots__ = ()

    name = 'foo'
    version = '1.foobar'
    log_id = name
    description = 'The first command'
    
    subcommands_title = 'Modes'
    subcommands_description = 'Various modes at your command'
    subcommands_help = 'Use --help after specifying a mode to get mode specific help'
    
    def _find_compatible_subcommands(self):
        cmds = super(MainCommand, self)._find_compatible_subcommands()
        assert len(cmds) == 1
        return cmds

# end class MainCommand


class SimpleSubcommand(SimpleCommand, SubCommandBase, bapp.plugin_type()):
    """A simple command to be used as subcommand"""
    __slots__ = ()
    
    main_command_name = MainCommand.name

# end class SimpleSubcommand

class IncompatibleSubccommand(SimpleSubcommand):
    """This one shouldn't be there"""
    __slots__ = ()
    
    name = 'notthisone'
    main_command_name = 'somethingelse'

# end class IncompatibleSubccommand


class TestCommands(TestCaseBase):
    """Basic command framework tests"""
    __slots__ = ()

    @with_application
    def test_simple_command(self):
        """Standard command features test"""
        cmd = SimpleCommand(application=bapp.main())
        assert cmd.parse_and_execute(list()) == cmd.ARGUMENT_ERROR, 'cannot execute without -x'
        assert cmd.parse_and_execute(['-h']) == cmd.ARGUMENT_HANDLED, 'can show help without error code'
        assert cmd.parse_and_execute(['--version']) == cmd.ARGUMENT_HANDLED, 'can show version'
        assert cmd.parse_and_execute(['-x', 'foo']) == 3, 'cannot use foo as int'
        assert cmd.parse_and_execute(['-x', '5']) == 0, 'first valid call'
        
    @with_application
    def test_master_command(self):
        """Simple subcommand testing"""
        cmd = MainCommand(application=bapp.main())
        cmd.parse_and_execute([]) == 1, 'auto-print usage for subcommands'
        cmd.parse_and_execute(['-h']) == cmd.ARGUMENT_HANDLED, 'can show help'
        cmd.parse_and_execute(['--version']) == cmd.ARGUMENT_HANDLED, 'can show version'
        cmd.parse_and_execute(['simple']) == 255, 'should require argument'
        cmd.parse_and_execute('simple -x foo'.split()) == 255, 'need int'
        cmd.parse_and_execute('simple -x 42'.split()) == 0, 'should be good'
        cmd.parse_and_execute('simple -x 42 --extra'.split()) == 1, 'extra args not allowed  by default'
        MainCommand.allow_unknown_args = True
        cmd.parse_and_execute('simple -x 42 --extra'.split()) == 0, 'can allow extra args'
        MainCommand.allow_unknown_args = False

        assert InputError, "Let's be sure this makes it into bcmd"

# end class TestCommands
