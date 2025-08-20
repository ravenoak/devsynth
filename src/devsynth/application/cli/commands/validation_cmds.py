"""Register validation-related CLI commands."""

from ..registry import register
from .validate_manifest_cmd import validate_manifest_cmd
from .validate_metadata_cmd import validate_metadata_cmd

register("validate-manifest", validate_manifest_cmd)
register("validate-metadata", validate_metadata_cmd)

__all__ = ["validate_manifest_cmd", "validate_metadata_cmd"]
