"""Diagnostic and system check commands."""

from ..registry import register
from .doctor_cmd import doctor_cmd


def check_cmd(config_dir: str = "config", quick: bool = False) -> None:
    """Alias for :func:`doctor_cmd` to maintain backward compatibility."""
    doctor_cmd(config_dir=config_dir, quick=quick)


register("doctor", doctor_cmd)
register("check", check_cmd)

__all__ = ["doctor_cmd", "check_cmd"]
