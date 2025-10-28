"""
Deterministic and timeout-related testing fixtures.

These fixtures centralize common test controls:
- deterministic_seed: sets RNG seeds across stdlib, NumPy, PyTorch; exports
  DEVSYNTH_TEST_SEED and PYTHONHASHSEED for subprocesses.
- enforce_test_timeout: optional per-test timeout controlled via
  DEVSYNTH_TEST_TIMEOUT_SECONDS.

They are imported by tests/conftest.py and intentionally kept separate to
improve maintainability (docs/tasks.md item 61) without changing behavior.
"""

from __future__ import annotations

import logging
import os
import random
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session", autouse=True)
def deterministic_seed() -> int:
    """Ensure deterministic behavior across tests by setting global RNG seeds.

    Environment variables:
    - DEVSYNTH_TEST_SEED: overrides the default seed (defaults to "1337").
    - PYTHONHASHSEED: exported for subprocess determinism when not already set.

    Returns:
    - The integer seed applied.
    """
    logger = logging.getLogger("tests.deterministic_seed")

    seed_env = os.environ.get("DEVSYNTH_TEST_SEED", "1337")
    try:
        seed = int(seed_env)
    except ValueError:
        logger.warning("Invalid DEVSYNTH_TEST_SEED=%r; falling back to 1337", seed_env)
        seed = 1337
        os.environ["DEVSYNTH_TEST_SEED"] = str(seed)

    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = str(seed)
        logger.debug("Set PYTHONHASHSEED=%s for subprocess determinism", seed)

    random.seed(seed)

    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception as e:  # pragma: no cover - optional dep
        logger.debug("NumPy not available or failed to seed: %s", e)

    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if getattr(torch, "cuda", None) and torch.cuda.is_available():  # type: ignore[attr-defined]
            try:
                torch.cuda.manual_seed_all(seed)  # type: ignore[attr-defined]
            except Exception as ce:  # pragma: no cover - optional env
                logger.debug("Failed to seed CUDA RNGs: %s", ce)
        try:
            import torch.backends.cudnn as cudnn  # type: ignore

            cudnn.deterministic = True  # type: ignore[attr-defined]
            cudnn.benchmark = False  # type: ignore[attr-defined]
        except Exception as be:  # pragma: no cover - optional env
            logger.debug("Failed to set cuDNN deterministic flags: %s", be)
    except Exception as e:  # pragma: no cover - optional dep
        logger.debug("PyTorch not available or failed to seed: %s", e)

    os.environ["DEVSYNTH_TEST_SEED"] = str(seed)
    logger.info("Deterministic test seed set to %s", seed)
    return seed


@pytest.fixture(autouse=True)
def enforce_test_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None]:
    """Enforce a per-test timeout when configured.

    Controlled by the environment variable DEVSYNTH_TEST_TIMEOUT_SECONDS.
    Uses signal.SIGALRM when available (POSIX). No-ops on unsupported platforms
    or when the variable is unset/non-positive.
    """
    timeout: int | None = None
    timeout_str = os.environ.get("DEVSYNTH_TEST_TIMEOUT_SECONDS")
    if timeout_str is not None:
        try:
            timeout = int(timeout_str)
        except Exception:
            timeout = None

    try:
        import signal  # type: ignore

        has_sigalrm = hasattr(signal, "SIGALRM")
    except Exception:  # pragma: no cover - platform specific
        signal = None  # type: ignore
        has_sigalrm = False

    if not timeout or timeout <= 0 or not has_sigalrm:
        yield
        return

    def _handler(signum, frame):  # noqa: ARG001 - signature required by signal
        raise RuntimeError(
            f"Test timed out after {timeout} seconds (DEVSYNTH_TEST_TIMEOUT_SECONDS)"
        )

    original = signal.getsignal(signal.SIGALRM)  # type: ignore[attr-defined]
    signal.signal(signal.SIGALRM, _handler)  # type: ignore[attr-defined]
    signal.alarm(timeout)  # type: ignore[attr-defined]
    try:
        yield
    finally:
        try:
            signal.alarm(0)  # type: ignore[attr-defined]
            signal.signal(signal.SIGALRM, original)  # type: ignore[attr-defined]
        except Exception:
            pass
