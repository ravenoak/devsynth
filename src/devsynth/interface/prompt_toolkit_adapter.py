"""Optional prompt-toolkit powered helpers for CLI interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type, cast, assert_type
from collections.abc import Callable, Iterable, Sequence

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)

# Type ignore for complex optional dependency typing issues
# The code works correctly at runtime, mypy struggles with conditional imports


@dataclass
class PromptToolkitComponents:
    """Container for prompt-toolkit primitives used by the adapter."""

    prompt_session_class: Any
    history_class: Any
    word_completer_class: Any
    radiolist_dialog: Any
    checkboxlist_dialog: Any
    style_class: Any
    complete_style_enum: Any


try:  # pragma: no cover - optional dependency import guard
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.shortcuts import checkboxlist_dialog, radiolist_dialog
    from prompt_toolkit.shortcuts.prompt import CompleteStyle
    from prompt_toolkit.styles import Style
except Exception:  # pragma: no cover - degrade gracefully when unavailable
    _PROMPT_TOOLKIT_COMPONENTS: PromptToolkitComponents | None = None
else:  # pragma: no cover - exercised in integration environments
    _PROMPT_TOOLKIT_COMPONENTS = PromptToolkitComponents(
        prompt_session_class=PromptSession,
        history_class=InMemoryHistory,
        word_completer_class=WordCompleter,
        radiolist_dialog=radiolist_dialog,
        checkboxlist_dialog=checkboxlist_dialog,
        style_class=Style,
        complete_style_enum=CompleteStyle,
    )


class PromptToolkitUnavailableError(RuntimeError):
    """Raised when prompt-toolkit features are requested but unavailable."""


class PromptToolkitAdapter:
    """Wrapper around prompt-toolkit sessions providing CLI niceties."""

    _components: PromptToolkitComponents

    def __init__(
        self,
        *,
        components: PromptToolkitComponents | None = None,
        session: Any | None = None,
    ) -> None:
        temp_components = components or _PROMPT_TOOLKIT_COMPONENTS
        if temp_components is None:
            raise PromptToolkitUnavailableError("prompt_toolkit is not installed")
        # After this check, _components is guaranteed to be not None
        self._components = temp_components

        self._history = self._components.history_class()
        self._session = session or self._components.prompt_session_class(
            history=self._history
        )
        self._dialog_style = (
            self._components.style_class.from_dict(
                {
                    "dialog": "bg:#1f1f1f #ffffff",
                    "dialog frame.label": "bg:#005f87 #ffffff",
                    "dialog.body": "bg:#1f1f1f #d7d7d7",
                    "button.focused": "bg:#005f87 #ffffff",
                }
            )
            if self._components.style_class is not None
            else None
        )

    @staticmethod
    def is_available() -> bool:
        """Return ``True`` when prompt-toolkit primitives are importable."""

        return _PROMPT_TOOLKIT_COMPONENTS is not None

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------
    def prompt_text(
        self,
        message: str,
        *,
        choices: Sequence[str | tuple[str, str]] | None = None,
        default: str | None = None,
        show_default: bool = True,
        validator: Callable[[str], bool] | None = None,
    ) -> str:
        """Prompt the user for text input with optional completions."""

        normalized_choices = self._normalize_choice_pairs(choices)
        if normalized_choices:
            selection = self.prompt_choice(message, normalized_choices, default=default)
            if selection is not None:
                return selection

        prompt_kwargs: dict[str, Any] = {}
        if normalized_choices:
            words = [value for value, _ in normalized_choices]
            prompt_kwargs["completer"] = self._components.word_completer_class(
                words, ignore_case=True
            )
            prompt_kwargs["complete_in_thread"] = True
            if self._components.complete_style_enum is not None:
                prompt_kwargs["complete_style"] = (
                    self._components.complete_style_enum.MULTI_COLUMN
                )

        prompt_message = self._format_prompt(message, default, show_default)

        response = self._invoke_prompt(prompt_message, default=default, **prompt_kwargs)
        response = self._coalesce_default(response, default)

        if validator is None:
            return response

        while True:
            try:
                if validator(response):
                    break
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug("Prompt validator raised an error: %s", exc)
                self._emit_validation_message(str(exc) or "Invalid input.")
            else:
                self._emit_validation_message(
                    "Invalid input. Please choose one of the available options."
                )

            response = self._invoke_prompt(
                prompt_message,
                default=default,
                **prompt_kwargs,
            )
            response = self._coalesce_default(response, default)

        return response

    def prompt_choice(
        self,
        message: str,
        choices: Sequence[tuple[str, str]],
        *,
        default: str | None = None,
    ) -> str | None:
        """Render a radio-list dialog for discrete selections."""

        if not choices:
            return default

        valid_values = [value for value, _ in choices]
        dialog_default = default if default in valid_values else None

        try:
            dialog = self._components.radiolist_dialog(
                title="DevSynth",
                text=message,
                values=choices,
                default=dialog_default,
                style=self._dialog_style,
            )
            result = dialog.run()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Radiolist dialog unavailable: %s", exc)
            return None

        if result is None:
            return None
        return str(result)

    def prompt_multi_select(
        self,
        message: str,
        *,
        options: Sequence[tuple[str, str]],
        default: Iterable[str] | None = None,
    ) -> list[str]:
        """Render a checkbox dialog allowing multiple selections."""

        default_values = [value for value in (default or [])]
        try:
            dialog = self._components.checkboxlist_dialog(
                title="DevSynth",
                text=message,
                values=list(options),
                default_values=default_values,
                style=self._dialog_style,
            )
            result = dialog.run()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Checkbox dialog unavailable: %s", exc)
            return list(default_values)

        if result is None:
            return list(default_values)
        return [str(item) for item in result]

    def confirm(self, message: str, *, default: bool = False) -> bool:
        """Prompt the user for confirmation using a radio dialog."""

        default_key = "yes" if default else "no"
        selection = self.prompt_choice(
            message,
            choices=[("yes", "Yes"), ("no", "No")],
            default=default_key,
        )
        if selection is None:
            return default
        return selection.lower() in {"y", "yes"}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _format_prompt(
        self, message: str, default: str | None, show_default: bool
    ) -> str:
        if default and show_default:
            return f"{message} [{default}]"
        return message

    def _invoke_prompt(
        self, message: str, *, default: str | None = None, **kwargs: Any
    ) -> str:
        try:
            result = self._session.prompt(message, default=default or "", **kwargs)
            return str(result)
        except (KeyboardInterrupt, EOFError):
            return default or ""

    @staticmethod
    def _coalesce_default(response: str, default: str | None) -> str:
        text = str(response).strip()
        if not text and default is not None:
            return default
        return text

    def _emit_validation_message(self, message: str) -> None:
        output = getattr(getattr(self._session, "app", None), "output", None)
        if output is not None and hasattr(output, "write"):
            try:  # pragma: no cover - depends on prompt-toolkit IO backend
                output.write(f"{message}\n")
                if hasattr(output, "flush"):
                    output.flush()
                return
            except Exception:  # pragma: no cover - defensive logging
                logger.debug("Unable to emit validation message", exc_info=True)
        logger.debug("Validation message: %s", message)

    @staticmethod
    def _normalize_choice_pairs(
        choices: Sequence[str | tuple[str, str]] | None,
    ) -> list[tuple[str, str]]:
        if not choices:
            return []
        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for choice in choices:
            if isinstance(choice, tuple):
                value, label = choice
            else:
                value = label = choice
            value_str = str(value)
            if value_str in seen:
                continue
            normalized.append((value_str, str(label)))
            seen.add(value_str)
        return normalized


_ADAPTER_SINGLETON: PromptToolkitAdapter | None = None


def get_prompt_toolkit_adapter() -> PromptToolkitAdapter | None:
    """Return a cached :class:`PromptToolkitAdapter` when available."""

    global _ADAPTER_SINGLETON
    if _ADAPTER_SINGLETON is not None:
        return _ADAPTER_SINGLETON

    if _PROMPT_TOOLKIT_COMPONENTS is None:
        return None

    try:
        _ADAPTER_SINGLETON = PromptToolkitAdapter()
    except PromptToolkitUnavailableError:
        _ADAPTER_SINGLETON = None
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.debug("Failed to initialise prompt-toolkit adapter: %s", exc)
        _ADAPTER_SINGLETON = None
    return _ADAPTER_SINGLETON


__all__ = [
    "PromptToolkitAdapter",
    "PromptToolkitComponents",
    "PromptToolkitUnavailableError",
    "get_prompt_toolkit_adapter",
]
