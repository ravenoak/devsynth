"""
API specification generation command for DevSynth.
"""

import os
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from typing import Dict, Any, List, Optional

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

console = Console()

def apispec_cmd(api_type: str = "rest", format_type: str = "openapi", name: str = "api", path: str = ".") -> None:
    """Generate an API specification for the specified API type and format."""
    try:
        # Show a welcome message for the apispec command
        console.print(Panel(
            f"[bold blue]DevSynth API Specification Generator[/bold blue]\n\n"
            f"This command will generate an API specification for a {api_type} API in {format_type} format.",
            title="API Specification Generator",
            border_style="blue"
        ))
        
        # Validate and normalize the API type
        api_type = api_type.lower()
        supported_api_types = ["rest", "graphql", "grpc"]
        
        if api_type not in supported_api_types:
            console.print(f"[yellow]Warning: '{api_type}' is not a recognized API type.[/yellow]")
            console.print(f"[yellow]Supported API types: {', '.join(supported_api_types)}[/yellow]")
            
            # Ask user to select an API type
            api_table = Table(title="Supported API Types")
            api_table.add_column("API Type", style="cyan")
            api_table.add_column("Description")
            
            api_table.add_row("rest", "RESTful API with HTTP methods and resources")
            api_table.add_row("graphql", "Query language and runtime for APIs")
            api_table.add_row("grpc", "High-performance RPC framework")
            
            console.print(api_table)
            
            api_type = Prompt.ask(
                "[blue]Select an API type[/blue]",
                choices=supported_api_types,
                default="rest"
            )
        
        # Validate and normalize the format
        format_type = format_type.lower()
        supported_formats = {
            "rest": ["openapi", "swagger", "raml"],
            "graphql": ["schema", "sdl"],
            "grpc": ["protobuf", "proto3"]
        }
        
        if format_type not in supported_formats.get(api_type, []):
            console.print(f"[yellow]Warning: '{format_type}' is not a recognized format for {api_type} API.[/yellow]")
            console.print(f"[yellow]Supported formats for {api_type}: {', '.join(supported_formats.get(api_type, []))}[/yellow]")
            
            # Ask user to select a format
            format_type = Prompt.ask(
                "[blue]Select a format[/blue]",
                choices=supported_formats.get(api_type, []),
                default=supported_formats.get(api_type, ["openapi"])[0]
            )
        
        # Get API name if not provided
        if name == "api":
            name = Prompt.ask("[blue]API name[/blue]", default="api")
        
        # Sanitize API name
        name = name.replace(" ", "_").lower()
        
        # Get API path if not provided
        if path == ".":
            path = Prompt.ask("[blue]API path[/blue]", default=".")
        
        # Create full API path
        api_path = os.path.join(path, f"{name}_api_spec")
        
        # Check if directory already exists
        if os.path.exists(api_path):
            if not Confirm.ask(f"[yellow]Directory {api_path} already exists. Overwrite?[/yellow]"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return
            
            # Remove existing directory
            shutil.rmtree(api_path)
        
        # Create API directory
        os.makedirs(api_path, exist_ok=True)
        
        # Get API information
        console.print("\n[bold]API Information[/bold]")
        
        # Get API version
        api_version = Prompt.ask("[blue]API version[/blue]", default="1.0.0")
        
        # Get API description
        api_description = Prompt.ask("[blue]API description[/blue]", default=f"API for {name}")
        
        # Show progress during generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            console=console
        ) as progress:
            # Create task for API specification generation
            task = progress.add_task(f"[blue]Generating {api_type} API specification...", total=100)
            
            # Generate API specification based on type and format
            if api_type == "rest":
                if format_type == "openapi" or format_type == "swagger":
                    # Create OpenAPI specification
                    spec_file = os.path.join(api_path, f"{name}_openapi.yaml")
                    with open(spec_file, "w") as f:
                        openapi_content = f"""openapi: 3.0.0
info:
  title: {name.capitalize()} API
  description: {api_description}
  version: {api_version}
servers:
  - url: https://api.example.com/v1
    description: Production server
paths:
  /users:
    get:
      summary: Get all users
      description: Returns a list of all users
      responses:
        '200':
          description: A list of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      summary: Create a new user
      description: Creates a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewUser'
      responses:
        '201':
          description: The created user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
  /users/{{id}}:
    get:
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: A user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
      required:
        - id
        - name
        - email
    NewUser:
      type: object
      properties:
        name:
          type: string
        email:
          type: string
      required:
        - name
        - email
"""
                        f.write(openapi_content)
                elif format_type == "raml":
                    # Create RAML specification
                    spec_file = os.path.join(api_path, f"{name}.raml")
                    with open(spec_file, "w") as f:
                        raml_content = f"""#%RAML 1.0
title: {name.capitalize()} API
description: {api_description}
version: {api_version}
baseUri: https://api.example.com/v1
mediaType: application/json

types:
  User:
    type: object
    properties:
      id: string
      name: string
      email: string
    required: [id, name, email]
  
  NewUser:
    type: object
    properties:
      name: string
      email: string
    required: [name, email]

/users:
  get:
    description: Get all users
    responses:
      200:
        body:
          application/json:
            type: array
            items: User
  post:
    description: Create a new user
    body:
      application/json:
        type: NewUser
    responses:
      201:
        body:
          application/json:
            type: User
  /{{id}}:
    get:
      description: Get a user by ID
      responses:
        200:
          body:
            application/json:
              type: User
"""
                        f.write(raml_content)
            
            elif api_type == "graphql":
                # Create GraphQL schema
                spec_file = os.path.join(api_path, f"{name}_schema.graphql")
                with open(spec_file, "w") as f:
                    graphql_content = f"""# {name.capitalize()} GraphQL Schema
# {api_description}
# Version: {api_version}

type User {{
  id: ID!
  name: String!
  email: String!
}}

input NewUser {{
  name: String!
  email: String!
}}

type Query {{
  users: [User!]!
  user(id: ID!): User
}}

type Mutation {{
  createUser(input: NewUser!): User!
  updateUser(id: ID!, input: NewUser!): User
  deleteUser(id: ID!): Boolean!
}}

schema {{
  query: Query
  mutation: Mutation
}}
"""
                    f.write(graphql_content)
            
            elif api_type == "grpc":
                # Create Protocol Buffers schema
                spec_file = os.path.join(api_path, f"{name}.proto")
                with open(spec_file, "w") as f:
                    proto_content = f"""syntax = "proto3";

package {name};

// {api_description}
// Version: {api_version}

service UserService {{
  rpc GetUsers(GetUsersRequest) returns (GetUsersResponse);
  rpc GetUser(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
}}

message User {{
  string id = 1;
  string name = 2;
  string email = 3;
}}

message GetUsersRequest {{
  // Empty request
}}

message GetUsersResponse {{
  repeated User users = 1;
}}

message GetUserRequest {{
  string id = 1;
}}

message CreateUserRequest {{
  string name = 1;
  string email = 2;
}}

message UpdateUserRequest {{
  string id = 1;
  string name = 2;
  string email = 3;
}}

message DeleteUserRequest {{
  string id = 1;
}}

message DeleteUserResponse {{
  bool success = 1;
}}
"""
                    f.write(proto_content)
            
            # Mark task as complete
            progress.update(task, completed=True)
        
        console.print(f"[green]✓ API specification generated successfully at: {api_path}[/green]")
        
        # Show next steps based on the API type and format
        console.print("\n[bold blue]Next Steps:[/bold blue]")
        
        if api_type == "rest":
            if format_type == "openapi" or format_type == "swagger":
                console.print("1. View your OpenAPI specification in Swagger UI")
                console.print("2. Generate client code from your specification")
            elif format_type == "raml":
                console.print("1. View your RAML specification in API Console")
        
        elif api_type == "graphql":
            console.print("1. Use your GraphQL schema with Apollo Server or other GraphQL servers")
        
        elif api_type == "grpc":
            console.print("1. Generate code from your Protocol Buffers definition")
        
    except Exception as err:
        console.print(f"[red]✗ Error:[/red] {str(err)}", highlight=False)
        console.print("[red]An unexpected error occurred during API specification generation.[/red]")
        
        # Show detailed error information
        import traceback
        console.print(Panel(
            traceback.format_exc(),
            title="Detailed Error Information",
            border_style="red"
        ))