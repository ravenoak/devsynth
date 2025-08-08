"""Commands related to artifact generation."""

from ..registry import register
from .code_cmd import code_cmd
from .spec_cmd import spec_cmd
from .test_cmd import test_cmd

register("spec", spec_cmd)
register("test", test_cmd)
register("code", code_cmd)

__all__ = ["spec_cmd", "test_cmd", "code_cmd"]
