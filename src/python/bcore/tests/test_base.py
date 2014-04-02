#-*-coding:utf-8-*-
"""
@package bcore.tests.test_base
@brief tests for bcore.base

@copyright 2012 Sebastian Thiel
"""
__all__ = []

from .base import (preserve_application,
                   TestCoreCaseBase)
                            
from butility import (InterfaceBase,
                      abstractmethod)

import bcore

from bcore import (InstanceNotFound,
                   TypeNotFound)


class TestCore(TestCoreCaseBase):
    __slots__ = ()
    
    @preserve_application
    def test_application(self):
        """Test BApplication functionality"""

        self.failUnlessRaises(EnvironmentError, bcore.app)

        class ICustomInterface(InterfaceBase):
            __slots__ = ()
            
            @abstractmethod
            def hello(self):
                return str()

        # end class ICustomInterface

        # It is possible to setup plugins even without an Application
        class CustomPluginType(ICustomInterface, bcore.plugin_type()):
            """Works without application"""
            __slots__ = ()
        
            def hello(self):
                return "world"
                
        # end class CustomPluginType

        # we don't have access to the stack without an application, so lets make one
        app = bcore.Application.new(setup_logging=False)
        assert bcore.Application.main is bcore.app() is app
        self.failUnlessRaises(InstanceNotFound, bcore.app().instance, file)
        self.failUnlessRaises(TypeNotFound, bcore.app().type, file)

        # As there is no instance, this one won't find one either
        self.failUnlessRaises(InstanceNotFound, bcore.app().instance, ICustomInterface)

        # the custom type can already be found
        assert bcore.app().type(ICustomInterface) is CustomPluginType

        # instance is cought by the associated context automatically. Early types will always go to the 
        # current main application
        inst = CustomPluginType()
        assert bcore.app().instance(ICustomInterface) is inst

    @preserve_application
    def test_hierarchical_loading(self):
        """See the hierarchical yaml loader in action"""
        assert bcore.Application.main is None
        app = bcore.Application.new(setup_logging=False, 
                                    settings_paths=(self.fixture_path(''),),
                                    settings_hierarchy=True)

        assert len(app.settings().data())

       
# end class TestCore
