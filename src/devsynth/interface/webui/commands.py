from __future__ import annotations

import importlib
import sys
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from devsynth.exceptions import DevSynthError

T = TypeVar("T")

try:  # pragma: no cover - optional dependency handling
    _cli_mod = importlib.import_module("devsynth.application.cli")  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _cli_mod = None

try:
    import devsynth.application.cli.utils as cli_utils
    from devsynth.application.cli import init_cmd, spec_cmd
except Exception:  # pragma: no cover - optional dependency
    init_cmd = None
    spec_cmd = None
    cli_utils = None  # type: ignore

try:  # pragma: no cover - optional dependency handling
    from devsynth.application.cli.commands.inspect_code_cmd import inspect_code_cmd
except Exception:  # pragma: no cover - optional dependency
    inspect_code_cmd = None
try:
    from devsynth.application.cli.commands.doctor_cmd import doctor_cmd
except Exception:  # pragma: no cover - optional dependency
    doctor_cmd = None
try:
    from devsynth.application.cli.commands.edrr_cycle_cmd import edrr_cycle_cmd
except Exception:  # pragma: no cover - optional dependency
    edrr_cycle_cmd = None
try:
    from devsynth.application.cli.commands.align_cmd import align_cmd
except Exception:  # pragma: no cover - optional dependency
    align_cmd = None
try:
    from devsynth.application.cli.commands.alignment_metrics_cmd import (
        alignment_metrics_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    alignment_metrics_cmd = None
try:
    from devsynth.application.cli.commands.inspect_config_cmd import inspect_config_cmd
except Exception:  # pragma: no cover - optional dependency
    inspect_config_cmd = None
try:
    from devsynth.application.cli.commands.validate_manifest_cmd import (
        validate_manifest_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    validate_manifest_cmd = None
try:
    from devsynth.application.cli.commands.validate_metadata_cmd import (
        validate_metadata_cmd,
    )
except Exception:  # pragma: no cover - optional dependency
    validate_metadata_cmd = None
try:
    from devsynth.application.cli.commands.test_metrics_cmd import test_metrics_cmd
except Exception:  # pragma: no cover - optional dependency
    test_metrics_cmd = None
try:
    from devsynth.application.cli.commands.generate_docs_cmd import generate_docs_cmd
except Exception:  # pragma: no cover - optional dependency
    generate_docs_cmd = None
try:
    from devsynth.application.cli.ingest_cmd import ingest_cmd
except Exception:  # pragma: no cover - optional dependency
    ingest_cmd = None
try:
    from devsynth.application.cli.apispec import apispec_cmd
except Exception:  # pragma: no cover - optional dependency
    apispec_cmd = None
try:
    from devsynth.application.cli.setup_wizard import SetupWizard
except Exception:  # pragma: no cover - optional dependency
    SetupWizard = None


class CommandHandlingMixin:
    """Utility mixin that provides CLI command lookup and execution helpers."""

    def _cli(self, name: str):
        """Return a CLI command by name if available."""

        module = sys.modules.get("devsynth.interface.webui")
        if module and hasattr(module, name):
            cmd = getattr(module, name)
            if cmd is not None:
                return cmd

        local_cmd = globals().get(name)
        if local_cmd is not None:
            return local_cmd

        if _cli_mod:
            return getattr(_cli_mod, name, None)
        return None

    def _handle_command_errors(
        self,
        func: Callable[..., T],
        error_message: str = "An error occurred",
        *args: Any,
        **kwargs: Any,
    ) -> T | None:
        """Execute a command with error handling."""

        try:
            return func(*args, **kwargs)
        except FileNotFoundError as exc:
            self.display_result(
                f"ERROR: File not found: {exc.filename}",
                highlight=False,
                message_type="error",
            )
            self.display_result(
                "Make sure the file exists and the path is correct.",
                highlight=False,
            )
            return None
        except PermissionError as exc:
            self.display_result(
                f"ERROR: Permission denied: {exc.filename}",
                highlight=False,
                message_type="error",
            )
            self.display_result(
                "Make sure you have the necessary permissions to access this file.",
                highlight=False,
                message_type="info",
            )
            return None
        except ValueError as exc:
            self.display_result(
                f"ERROR: Invalid value: {exc}", highlight=False, message_type="error"
            )
            self.display_result(
                "Please check your input and try again.",
                highlight=False,
                message_type="info",
            )
            return None
        except KeyError as exc:
            self.display_result(
                f"ERROR: Missing key: {exc}", highlight=False, message_type="error"
            )
            self.display_result(
                "Verify that the referenced key exists and is spelled correctly.",
                highlight=False,
                message_type="info",
            )
            return None
        except TypeError as exc:
            self.display_result(
                f"ERROR: Type error: {exc}", highlight=False, message_type="error"
            )
            self.display_result(
                "Check that all inputs are of the expected type.",
                highlight=False,
                message_type="info",
            )
            return None
        except DevSynthError:
            raise
        except Exception as exc:  # noqa: BLE001
            formatted = self._format_error_message(exc)
            self.display_result(
                f"ERROR: {error_message}: {formatted}",
                highlight=False,
                message_type="error",
            )
            self._render_traceback(traceback.format_exc())
            return None


__all__ = [
    "CommandHandlingMixin",
    "align_cmd",
    "alignment_metrics_cmd",
    "apispec_cmd",
    "cli_utils",
    "doctor_cmd",
    "edrr_cycle_cmd",
    "generate_docs_cmd",
    "ingest_cmd",
    "init_cmd",
    "inspect_code_cmd",
    "inspect_config_cmd",
    "SetupWizard",
    "spec_cmd",
    "test_metrics_cmd",
    "validate_manifest_cmd",
    "validate_metadata_cmd",
]
