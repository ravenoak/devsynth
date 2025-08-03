# Fish shell completion for DevSynth CLI

# Define the main DevSynth commands
set -l commands init spec test code run config gather refactor inspect webapp serve dbschema doctor help

# Define options for each command
set -l init_opts --path --template --force --verbose
set -l spec_opts --requirements-file --output-file --verbose
set -l test_opts --spec-file --output-file --verbose
set -l code_opts --test-file --output-dir --language --verbose
set -l run_opts --target --verbose
set -l config_opts --key --value --list --verbose
set -l gather_opts --interactive --output-file --verbose
set -l refactor_opts --file --verbose
set -l inspect_opts --file --verbose
set -l webapp_opts --framework --output-dir --verbose
set -l serve_opts --host --port --verbose
set -l dbschema_opts --input-file --output-file --verbose
set -l doctor_opts --fix --verbose

# Define option arguments
set -l templates basic advanced webapp api
set -l languages python javascript typescript java csharp go rust
set -l frameworks flask django fastapi express react vue angular
set -l targets unit-tests integration-tests all
set -l config_keys model provider offline_mode memory_backend log_level

# Main command completion
complete -c devsynth -f
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "init" -d "Initialize a new DevSynth project"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "spec" -d "Generate specifications from requirements"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "test" -d "Generate tests from specifications"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "code" -d "Generate code from tests"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "run" -d "Execute the generated code"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "config" -d "Configure DevSynth settings"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "gather" -d "Gather project requirements interactively"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "refactor" -d "Suggest code refactoring"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "inspect" -d "Inspect and analyze code"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "webapp" -d "Generate a web application"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "serve" -d "Start the DevSynth API server"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "dbschema" -d "Generate database schema"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "doctor" -d "Check DevSynth environment"
complete -c devsynth -n "not __fish_seen_subcommand_from $commands" -a "help" -d "Show help information"

# Command-specific option completion
# init command
complete -c devsynth -n "__fish_seen_subcommand_from init" -l path -d "Path to initialize project" -r
complete -c devsynth -n "__fish_seen_subcommand_from init" -l template -d "Project template to use" -r -a "$templates"
complete -c devsynth -n "__fish_seen_subcommand_from init" -l force -d "Force initialization even if directory exists"
complete -c devsynth -n "__fish_seen_subcommand_from init" -l verbose -d "Enable verbose output"

# spec command
complete -c devsynth -n "__fish_seen_subcommand_from spec" -l requirements-file -d "Path to requirements file" -r
complete -c devsynth -n "__fish_seen_subcommand_from spec" -l output-file -d "Path to output specifications file" -r
complete -c devsynth -n "__fish_seen_subcommand_from spec" -l verbose -d "Enable verbose output"

# test command
complete -c devsynth -n "__fish_seen_subcommand_from test" -l spec-file -d "Path to specifications file" -r
complete -c devsynth -n "__fish_seen_subcommand_from test" -l output-file -d "Path to output tests file" -r
complete -c devsynth -n "__fish_seen_subcommand_from test" -l verbose -d "Enable verbose output"

# code command
complete -c devsynth -n "__fish_seen_subcommand_from code" -l test-file -d "Path to tests file" -r
complete -c devsynth -n "__fish_seen_subcommand_from code" -l output-dir -d "Directory for generated code" -r
complete -c devsynth -n "__fish_seen_subcommand_from code" -l language -d "Programming language for generated code" -r -a "$languages"
complete -c devsynth -n "__fish_seen_subcommand_from code" -l verbose -d "Enable verbose output"

# run command
complete -c devsynth -n "__fish_seen_subcommand_from run" -l target -d "Target to run" -r -a "$targets"
complete -c devsynth -n "__fish_seen_subcommand_from run" -l verbose -d "Enable verbose output"

# config command
complete -c devsynth -n "__fish_seen_subcommand_from config" -l key -d "Configuration key" -r -a "$config_keys"
complete -c devsynth -n "__fish_seen_subcommand_from config" -l value -d "Configuration value" -r
complete -c devsynth -n "__fish_seen_subcommand_from config" -l list -d "List all configuration settings"
complete -c devsynth -n "__fish_seen_subcommand_from config" -l verbose -d "Enable verbose output"

# gather command
complete -c devsynth -n "__fish_seen_subcommand_from gather" -l interactive -d "Run in interactive mode"
complete -c devsynth -n "__fish_seen_subcommand_from gather" -l output-file -d "Path to output requirements file" -r
complete -c devsynth -n "__fish_seen_subcommand_from gather" -l verbose -d "Enable verbose output"

# refactor command
complete -c devsynth -n "__fish_seen_subcommand_from refactor" -l file -d "Path to file to refactor" -r
complete -c devsynth -n "__fish_seen_subcommand_from refactor" -l verbose -d "Enable verbose output"

# inspect command
complete -c devsynth -n "__fish_seen_subcommand_from inspect" -l file -d "Path to file to inspect" -r
complete -c devsynth -n "__fish_seen_subcommand_from inspect" -l verbose -d "Enable verbose output"

# webapp command
complete -c devsynth -n "__fish_seen_subcommand_from webapp" -l framework -d "Web framework to use" -r -a "$frameworks"
complete -c devsynth -n "__fish_seen_subcommand_from webapp" -l output-dir -d "Directory for generated webapp" -r
complete -c devsynth -n "__fish_seen_subcommand_from webapp" -l verbose -d "Enable verbose output"

# serve command
complete -c devsynth -n "__fish_seen_subcommand_from serve" -l host -d "Host to bind to" -r
complete -c devsynth -n "__fish_seen_subcommand_from serve" -l port -d "Port to listen on" -r
complete -c devsynth -n "__fish_seen_subcommand_from serve" -l verbose -d "Enable verbose output"

# dbschema command
complete -c devsynth -n "__fish_seen_subcommand_from dbschema" -l input-file -d "Path to input file" -r
complete -c devsynth -n "__fish_seen_subcommand_from dbschema" -l output-file -d "Path to output schema file" -r
complete -c devsynth -n "__fish_seen_subcommand_from dbschema" -l verbose -d "Enable verbose output"

# doctor command
complete -c devsynth -n "__fish_seen_subcommand_from doctor" -l fix -d "Attempt to fix issues"
complete -c devsynth -n "__fish_seen_subcommand_from doctor" -l verbose -d "Enable verbose output"

# help command
complete -c devsynth -n "__fish_seen_subcommand_from help" -a "$commands" -d "Show help for command"