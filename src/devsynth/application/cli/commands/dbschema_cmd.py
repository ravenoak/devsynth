"""[experimental] Generate a database schema for the specified database type.

This generator provides basic schemas; production-grade outputs may require manual adjustments.
"""

from __future__ import annotations

import os
import shutil
from typing import Optional

from rich.panel import Panel
from rich.table import Table

from devsynth.interface.ux_bridge import UXBridge

from ..utils import _resolve_bridge


def dbschema_cmd(
    db_type: str = "sqlite",
    name: str = "database",
    path: str = ".",
    force: bool = False,
    *,
    bridge: UXBridge | None = None,
) -> None:
    """Generate a database schema for the specified database type."""
    bridge = _resolve_bridge(bridge)
    try:
        bridge.print(
            Panel(
                f"[bold blue]DevSynth Database Schema Generator[/bold blue]\n\n",
                f"This command will generate a database schema for {db_type}.",
                title="Database Schema Generator",
                border_style="blue",
            )
        )

        db_type = db_type.lower()
        supported_db_types = ["sqlite", "mysql", "postgresql", "mongodb"]
        if db_type not in supported_db_types:
            raise ValueError(
                f"Unsupported database type '{db_type}'. Supported: {', '.join(supported_db_types)}"
            )

        name = name.replace(" ", "_").lower()
        schema_path = os.path.join(path, f"{name}_schema")

        if os.path.exists(schema_path):
            if not force:
                bridge.display_result(
                    f"[yellow]Directory {schema_path} already exists. Use --force to overwrite.[/yellow]"
                )
                return
            shutil.rmtree(schema_path)

        os.makedirs(schema_path, exist_ok=True)

        if db_type in ["sqlite", "mysql", "postgresql"]:
            entities = [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "type": "integer",
                            "constraints": ["PRIMARY KEY"],
                        },
                        {
                            "name": "username",
                            "type": "text",
                            "constraints": ["NOT NULL", "UNIQUE"],
                        },
                        {
                            "name": "email",
                            "type": "text",
                            "constraints": ["NOT NULL", "UNIQUE"],
                        },
                        {
                            "name": "password",
                            "type": "text",
                            "constraints": ["NOT NULL"],
                        },
                        {
                            "name": "created_at",
                            "type": "datetime",
                            "constraints": ["NOT NULL"],
                        },
                    ],
                },
                {
                    "name": "posts",
                    "fields": [
                        {
                            "name": "id",
                            "type": "integer",
                            "constraints": ["PRIMARY KEY"],
                        },
                        {
                            "name": "user_id",
                            "type": "integer",
                            "constraints": ["NOT NULL"],
                        },
                        {"name": "title", "type": "text", "constraints": ["NOT NULL"]},
                        {
                            "name": "content",
                            "type": "text",
                            "constraints": ["NOT NULL"],
                        },
                        {
                            "name": "created_at",
                            "type": "datetime",
                            "constraints": ["NOT NULL"],
                        },
                    ],
                },
            ]
        else:
            entities = [
                {
                    "name": "users",
                    "fields": [
                        {"name": "_id", "type": "objectId", "constraints": []},
                        {
                            "name": "username",
                            "type": "string",
                            "constraints": ["required: true", "unique: true"],
                        },
                        {
                            "name": "email",
                            "type": "string",
                            "constraints": ["required: true", "unique: true"],
                        },
                        {
                            "name": "password",
                            "type": "string",
                            "constraints": ["required: true"],
                        },
                        {
                            "name": "created_at",
                            "type": "date",
                            "constraints": ["required: true"],
                        },
                    ],
                },
                {
                    "name": "posts",
                    "fields": [
                        {"name": "_id", "type": "objectId", "constraints": []},
                        {
                            "name": "user_id",
                            "type": "objectId",
                            "constraints": ["required: true"],
                        },
                        {
                            "name": "title",
                            "type": "string",
                            "constraints": ["required: true"],
                        },
                        {
                            "name": "content",
                            "type": "string",
                            "constraints": ["required: true"],
                        },
                        {
                            "name": "created_at",
                            "type": "date",
                            "constraints": ["required: true"],
                        },
                    ],
                },
            ]

        with bridge.create_progress(
            f"Generating {db_type} schema...", total=100
        ) as progress:
            if db_type == "sqlite":
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- SQLite schema for {name}\n\n")
                    for entity in entities:
                        f.write(f"CREATE TABLE {entity['name']} (\n")
                        field_definitions = []
                        for field in entity["fields"]:
                            field_def = f"    {field['name']} {field['type'].upper()}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)
                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")
                progress.update(advance=100)
            elif db_type == "mysql":
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- MySQL schema for {name}\n\n")
                    f.write(f"CREATE DATABASE IF NOT EXISTS {name};\n")
                    f.write(f"USE {name};\n\n")
                    for entity in entities:
                        f.write(f"CREATE TABLE {entity['name']} (\n")
                        field_definitions = []
                        for field in entity["fields"]:
                            field_def = f"    {field['name']} {field['type'].upper()}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)
                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")
                progress.update(advance=100)
            elif db_type == "postgresql":
                schema_file = os.path.join(schema_path, f"{name}_schema.sql")
                with open(schema_file, "w") as f:
                    f.write(f"-- PostgreSQL schema for {name}\n\n")
                    f.write(f"CREATE SCHEMA IF NOT EXISTS {name};\n\n")
                    for entity in entities:
                        f.write(f"CREATE TABLE {name}.{entity['name']} (\n")
                        field_definitions = []
                        for field in entity["fields"]:
                            pg_type = field["type"].upper()
                            if pg_type == "INTEGER":
                                pg_type = (
                                    "SERIAL"
                                    if "PRIMARY KEY" in field["constraints"]
                                    else "INTEGER"
                                )
                            elif pg_type == "TEXT":
                                pg_type = "VARCHAR(255)"
                            field_def = f"    {field['name']} {pg_type}"
                            if field["constraints"]:
                                field_def += f" {' '.join(field['constraints'])}"
                            field_definitions.append(field_def)
                        f.write(",\n".join(field_definitions))
                        f.write("\n);\n\n")
                progress.update(advance=100)
            else:
                schema_file = os.path.join(schema_path, f"{name}_schema.js")
                with open(schema_file, "w") as f:
                    f.write(f"// MongoDB schema for {name} using Mongoose\n\n")
                    f.write("const mongoose = require('mongoose');\n")
                    f.write("const Schema = mongoose.Schema;\n\n")
                    for entity in entities:
                        f.write(f"// {entity['name']} schema\n")
                        f.write(f"const {entity['name']}Schema = new Schema({{\n")
                        field_definitions = []
                        for field in entity["fields"]:
                            if field["name"] == "_id":
                                continue
                            mongoose_type = field["type"]
                            if mongoose_type == "string":
                                mongoose_type = "String"
                            elif mongoose_type == "number":
                                mongoose_type = "Number"
                            elif mongoose_type == "boolean":
                                mongoose_type = "Boolean"
                            elif mongoose_type == "date":
                                mongoose_type = "Date"
                            elif mongoose_type == "objectId":
                                mongoose_type = "Schema.Types.ObjectId"
                            elif mongoose_type == "array":
                                mongoose_type = "[]"
                            elif mongoose_type == "object":
                                mongoose_type = "{}"
                            if field["constraints"]:
                                field_def = f"    {field['name']}: {{\n"
                                field_def += f"        type: {mongoose_type},\n"
                                for constraint in field["constraints"]:
                                    field_def += f"        {constraint},\n"
                                field_def += "    }"
                            else:
                                field_def = f"    {field['name']}: {mongoose_type}"
                            field_definitions.append(field_def)
                        f.write(",\n".join(field_definitions))
                        f.write("\n}, { timestamps: true });\n\n")
                        f.write(
                            f"const {entity['name'].capitalize()} = mongoose.model('{entity['name'].capitalize()}', {entity['name']}Schema);\n\n"
                        )
                    f.write("module.exports = {\n")
                    exports = [
                        f"    {entity['name'].capitalize()}" for entity in entities
                    ]
                    f.write(",\n".join(exports))
                    f.write("\n};\n")
                progress.update(advance=100)
            progress.complete()

        bridge.display_result(
            f"[green]\u2713 Database schema generated successfully at: {schema_path}[/green]"
        )

        bridge.display_result("\n[bold blue]Next Steps:[/bold blue]")
        if db_type == "sqlite":
            bridge.display_result("1. Use the schema to create your SQLite database:")
            bridge.display_result(
                f"   [green]sqlite3 {name}.db < {schema_file}[/green]"
            )
        elif db_type == "mysql":
            bridge.display_result("1. Use the schema to create your MySQL database:")
            bridge.display_result(
                f"   [green]mysql -u username -p < {schema_file}[/green]"
            )
        elif db_type == "postgresql":
            bridge.display_result(
                "1. Use the schema to create your PostgreSQL database:"
            )
            bridge.display_result(
                f"   [green]psql -U username -d {name} -f {schema_file}[/green]"
            )
        elif db_type == "mongodb":
            bridge.display_result("1. Install Mongoose in your Node.js project:")
            bridge.display_result(f"   [green]npm install mongoose[/green]")
            bridge.display_result("2. Import the schema in your application:")
            bridge.display_result(
                f"   [green]const {{ {', '.join([entity['name'].capitalize() for entity in entities])} }} = require('./path/to/{name}_schema.js');[/green]"
            )

    except Exception as err:
        bridge.display_result(f"[red]\u2717 Error:[/red] {str(err)}", highlight=False)
        bridge.display_result(
            "[red]An unexpected error occurred during database schema generation.[/red]"
        )

        import traceback

        bridge.print(
            Panel(
                traceback.format_exc(),
                title="Detailed Error Information",
                border_style="red",
            )
        )


__all__ = ["dbschema_cmd"]
