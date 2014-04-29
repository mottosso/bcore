#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_base
@brief tests for bprocess

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = []

if __name__ == '__main__':
    print sys.argv

import sys
import os
import tempfile

import bapp

from butility.tests import TestCaseBase
from bprocess import *
from bapp.tests import preserve_application
from butility import Path

import subprocess


class TestCommand(object):
    """Create a marker file upon execution"""
    __slots__ = ()
    
    marker = Path(tempfile.mktemp())
    
    def execute(self):
        self.marker.touch()
        # Output for the delegate to receive
        print self.marker

# end class TestCommand


class ITestMarkerInterface(object):
    """Just a marker to find something in the registry"""
    __slots__ = ()

    

# end class CustomTestInterface


class TestPluginLoading(object):
    """Setup an application and try to use a very specific plugin"""
    __slots__ = ()

    def execute(self):
        assert len(sys.argv) == 2
        use_settings = sys.argv[1] == 'settings'

        app = ProcessAwareApplication.new(load_plugins_from_settings = use_settings,
                                          load_plugins_from_trees = not use_settings)
        # that would only work if the plugin was loaded
        app.new_instance(ITestMarkerInterface)

# end class TestPluginLoading


class TestProcessController(ProcessController):
    """A controller tuned not to 'break out' of the test-sandbox by traversing up the hierarchy"""
    __slots__ = ()

    traverse_process_path_hierachy = False
    traverse_additional_path_hierachies = False
    load_user_settings = False

# end class TestProcessController


def pseudo_executable(bin_name):
    """@return full path to pseudo_executable based on the given executable basename"""
    return Path(__file__).dirname() / bin_name


class TestProcessControl(TestCaseBase):
    """Tests for the process control engine"""
    __slots__ = ()
    
    @preserve_application
    def test_base(self):
        """test fundamentals"""
        # Now we could nicely mock the environment - lets do this once we have a CWD environment
        # For now its not too easy though
        # failure as foo cannot be found
        self.failUnlessRaises(EnvironmentError, lambda: ProcessController(pseudo_executable('foo'), ('hello', 'world')).application())

    @preserve_application
    def test_forced_spawn(self):
        """Verify that we can easily enforce a process to be spawned, without overwriting any 'natural' configuration"""
        pctrl = ProcessController(pseudo_executable('py-program'), list())
        assert pctrl.set_should_spawn_process_override(True) is None
        assert pctrl.execute().returncode == 0
    
    @preserve_application
    def test_python_execution(self):
        """we should be able to execute any code directly using the delegate, without spawning"""
        pctrl = TestProcessController(pseudo_executable('py-program'), list())
        
        process = pctrl.execute()
        assert process.returncode == 0
        
    @preserve_application
    def test_custom_args(self):
        """verify we can handle custom arguments"""
        cmd_path = pseudo_executable('py-program-overrides')
        self.failUnlessRaises(DisplayHelpException, ProcessController(cmd_path, '---foo=bar ---help'.split()).execute)
        
        self.failUnlessRaises(AssertionError, ProcessController(cmd_path, ['---foo']).execute)
        
        pctrl = ProcessController(cmd_path, '---foo=bar ---hello.world=42'.split())
        assert pctrl.execute().returncode == 0

        # Override the python version, to something that doesn't exist
        version = '0.2.3'
        assert pctrl.executable().endswith('2.6'), 'default is to be 2.6'
        pctrl = ProcessController(cmd_path, ('---packages.python.version=%s' % version).split())
        assert pctrl.executable().endswith(version), 'cmd line override should have worked'
        
    @preserve_application
    def test_execute_in_context(self):
        process = ProcessController(pseudo_executable('py-program'), ['--hello', 'world']).execute_in_current_context()
        assert process.returncode == 1, "should not have understood our arguments"
        
        # now with self-driven communication
        process = ProcessController(pseudo_executable('py-program')).execute_in_current_context(stdout=subprocess.PIPE)
        assert process.returncode is None
        # delete the file it creates
        os.remove(process.stdout.readlines()[0].strip())
        process.communicate()
        assert process.returncode == 0

    @preserve_application
    def test_delegate_finder(self):
        from .delegate import TestCommunicatorDelegate
        pctrl = ProcessController(pseudo_executable('py-program-no-delegate'))
        tcd_name = TestCommunicatorDelegate.__name__
        assert type(pctrl.delegate()).__name__ == tcd_name, "The delegate should be looked up from the alias"

        pctrl = ProcessController(pseudo_executable('py-program-delegate-via-requires'))
        assert type(pctrl.delegate()).__name__ == tcd_name

        # This one really tests remote configuration
        pctrl = ProcessController(pseudo_executable('py-program-delegate-via-requires-in-remote-config'), ('---trace', 
            '---foo=bar'))
        assert type(pctrl.delegate()).__name__ == 'TestOverridesDelegate'

    @preserve_application
    def test_process_plugin_loading(self):
        """Assure plugins are loaded from trees and using the settings"""
        for program in ('load-from-directories', 'load-from-settings'):
            pctrl = ProcessController(pseudo_executable(program))
            assert pctrl.execute_in_current_context().returncode == 0
        # end for each program to test

    @preserve_application
    def test_iteration(self):
        """verify simple package iteration works (for those who want it)"""
        count = 0
        program = 'py-program-overrides'
        executable = pseudo_executable(program)
        args = ('---trace',)
        for package in ProcessController(executable, args).iter_packages(program):
            count += 1
            assert isinstance(package, ProcessControllerPackageSpecification)
        # end for each package
        assert count > 1
        
        self.failUnlessRaises(EnvironmentError, ProcessController(executable, args).iter_packages('foobar').next)
        
    @preserve_application
    def test_post_launch_info(self):
        """Just some basic tests"""
        info = ControlledProcessInformation()
        if not info.has_data():
            assert info.data() is None and info.process_data() is None
        else:
            pinfo = info.process_data()
            assert pinfo.executable.isfile()
            assert pinfo.executable.dirname().isdir()
            assert pinfo.id
            app = ProcessAwareApplication.new()
            assert bapp.main().context().settings().value_by_schema(process_schema).executable == pinfo.executable
        # end handle data
        assert ProcessAwareApplication.process_information() is info, "process information should be a singleton"
        
# end class TestProcessControl
