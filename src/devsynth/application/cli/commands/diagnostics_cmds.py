"""Diagnostic and system check commands."""

from ..registry import register
from .doctor_cmd import doctor_cmd

check_cmd = doctor_cmd

register("doctor", doctor_cmd)
register("check", check_cmd)

__all__ = ["doctor_cmd", "check_cmd"]
