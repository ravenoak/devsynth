"""User interface related commands."""

from ..registry import register
from .dbschema_cmd import dbschema_cmd
from .dpg_cmd import dpg_cmd
from .serve_cmd import serve_cmd
from .webapp_cmd import webapp_cmd
from .webui_cmd import webui_cmd

register("webapp", webapp_cmd)
register("serve", serve_cmd)
register("dbschema", dbschema_cmd)
register("webui", webui_cmd)
register("dpg", dpg_cmd)

__all__ = ["webapp_cmd", "serve_cmd", "dbschema_cmd", "webui_cmd", "dpg_cmd"]
