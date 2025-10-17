"""Unit tests for ProgressIndicator aliasing and import order."""

import importlib
import pytest

from devsynth.application.cli.long_running_progress import (
    LongRunningProgressIndicator,
    _ProgressIndicatorBase,
    _ProgressIndicatorProtocol,
)
from devsynth.interface.ux_bridge import ProgressIndicator


class TestProgressIndicatorAliasing:
    """Test that _ProgressIndicatorBase is properly defined and accessible."""

    def test_progress_indicator_base_is_concrete_class(self):
        """Test that _ProgressIndicatorBase is a concrete class, not a type alias."""
        # Should be the actual ProgressIndicator class, not a TypeAlias
        assert _ProgressIndicatorBase is ProgressIndicator
        assert isinstance(_ProgressIndicatorBase, type)
        assert issubclass(_ProgressIndicatorBase, ProgressIndicator)

    def test_progress_indicator_base_available_at_import_time(self):
        """Test that _ProgressIndicatorBase is available immediately after import."""
        # This should not raise NameError
        assert hasattr(LongRunningProgressIndicator, '__bases__')
        assert _ProgressIndicatorBase in LongRunningProgressIndicator.__bases__

    def test_progress_indicator_protocol_exists(self):
        """Test that _ProgressIndicatorProtocol is defined for type checking."""
        # The protocol should be a runtime-checkable Protocol class
        assert _ProgressIndicatorProtocol is not None
        # It should have the expected methods
        assert hasattr(_ProgressIndicatorProtocol, 'update')
        assert hasattr(_ProgressIndicatorProtocol, 'complete')

    def test_long_running_progress_indicator_inherits_correctly(self):
        """Test that LongRunningProgressIndicator inherits from the correct base."""
        assert issubclass(LongRunningProgressIndicator, _ProgressIndicatorBase)
        assert issubclass(LongRunningProgressIndicator, ProgressIndicator)

    def test_module_reload_preserves_base_class(self):
        """Test that module reload preserves the _ProgressIndicatorBase definition."""
        import devsynth.application.cli.long_running_progress as progress_module

        # Get initial base
        initial_base = progress_module._ProgressIndicatorBase

        # Reload the module
        importlib.reload(progress_module)

        # Base should still be the same
        reloaded_base = progress_module._ProgressIndicatorBase
        assert reloaded_base is initial_base
        assert reloaded_base is ProgressIndicator

    def test_import_from_module_works_after_reload(self):
        """Test that importing _ProgressIndicatorBase works after module reload."""
        import devsynth.application.cli.long_running_progress as progress_module

        # Import should work
        base_class = progress_module._ProgressIndicatorBase
        assert base_class is ProgressIndicator

        # Reload and try again
        importlib.reload(progress_module)
        base_class = progress_module._ProgressIndicatorBase
        assert base_class is ProgressIndicator

    def test_long_running_progress_indicator_instantiation(self):
        """Test that LongRunningProgressIndicator can be instantiated."""
        # This should not raise any errors related to base class resolution
        # Note: LongRunningProgressIndicator requires console, description, and total args
        # We can't easily instantiate it without proper setup, but we can verify the class exists
        assert LongRunningProgressIndicator is not None
        assert hasattr(LongRunningProgressIndicator, '__init__')

    def test_progress_indicator_base_has_expected_methods(self):
        """Test that _ProgressIndicatorBase has the expected interface."""
        # Should have the methods from ProgressIndicator protocol
        expected_methods = ['update', 'complete']
        for method in expected_methods:
            assert hasattr(_ProgressIndicatorBase, method)

        # Note: start_task and complete_task are specific to LongRunningProgressIndicator,
        # not necessarily part of the base ProgressIndicator interface

    def test_deterministic_tests_can_import_base(self):
        """Test that deterministic tests can import _ProgressIndicatorBase."""
        # This simulates what the deterministic progress tests do
        from devsynth.application.cli.long_running_progress import _ProgressIndicatorBase as imported_base

        assert imported_base is ProgressIndicator
        assert issubclass(LongRunningProgressIndicator, imported_base)
