#compdef devsynth
# Zsh completion script for DevSynth CLI

_devsynth() {
    local -a commands options
    local state

    # Main commands
    commands=(
        'init:Initialize a new DevSynth project'
        'spec:Generate specifications from requirements'
        'test:Generate tests from specifications'
        'code:Generate code from tests'
        'run-pipeline:Run the generated pipeline'
        'config:Configure DevSynth settings'
        'gather:Gather project requirements interactively'
        'refactor:Suggest code refactoring'
        'inspect:Inspect and analyze code'
        'webapp:Generate a web application'
        'serve:Start the DevSynth API server'
        'dbschema:Generate database schema'
        'doctor:Check DevSynth environment'
        'completion:Generate shell completion scripts'
        'help:Show help information'
    )

    # Command-specific options
    local -a init_opts spec_opts test_opts code_opts run_opts config_opts
    local -a gather_opts refactor_opts inspect_opts webapp_opts serve_opts dbschema_opts doctor_opts completion_opts

    init_opts=(
        '--wizard[Run in interactive wizard mode]'
        '--root=[Project root directory]:directory:_files -/'
        '--language=[Primary project language]'
        '--goals=[Project goals or description]'
        '--memory-backend=[Memory backend]:backend:(memory file kuzu chromadb)'
        '--offline-mode[Enable offline mode]'
        '--features=[Features to enable]:features:'
        '--auto-confirm[Skip confirmations]'
        '--defaults[Use default prompt values]'
        '--non-interactive[Run without prompts]'
        '--metrics-dashboard[Show metrics dashboard hint]'
    )

    spec_opts=(
        '--requirements-file=[Path to requirements file]:file:_files'
        '--output-file=[Path to output specifications file]:file:_files'
        '--verbose[Enable verbose output]'
    )

    test_opts=(
        '--spec-file=[Path to specifications file]:file:_files'
        '--output-file=[Path to output tests file]:file:_files'
        '--verbose[Enable verbose output]'
    )

    code_opts=(
        '--test-file=[Path to tests file]:file:_files'
        '--output-dir=[Directory for generated code]:directory:_files -/'
        '--language=[Programming language for generated code]:language:(python javascript typescript java csharp go rust)'
        '--verbose[Enable verbose output]'
    )

    run_opts=(
        '--target=[Target to run]:target:(unit-tests integration-tests all)'
        '--verbose[Enable verbose output]'
    )

    config_opts=(
        '--key=[Configuration key]:key:(model provider offline_mode memory_backend log_level)'
        '--value=[Configuration value]:value:'
        '--list[List all configuration settings]'
        '--verbose[Enable verbose output]'
    )

    gather_opts=(
        '--interactive[Run in interactive mode]'
        '--output-file=[Path to output requirements file]:file:_files'
        '--verbose[Enable verbose output]'
    )

    refactor_opts=(
        '--file=[Path to file to refactor]:file:_files'
        '--verbose[Enable verbose output]'
    )

    inspect_opts=(
        '--file=[Path to file to inspect]:file:_files'
        '--verbose[Enable verbose output]'
    )

    webapp_opts=(
        '--framework=[Web framework to use]:framework:(flask django fastapi express react vue angular)'
        '--output-dir=[Directory for generated webapp]:directory:_files -/'
        '--verbose[Enable verbose output]'
    )

    serve_opts=(
        '--host=[Host to bind to]:host:'
        '--port=[Port to listen on]:port:'
        '--verbose[Enable verbose output]'
    )

    dbschema_opts=(
        '--input-file=[Path to input file]:file:_files'
        '--output-file=[Path to output schema file]:file:_files'
        '--verbose[Enable verbose output]'
    )

    doctor_opts=(
        '--fix[Attempt to fix issues]'
        '--verbose[Enable verbose output]'
    )
    completion_opts=(
        '--shell=[Target shell]:shell:(bash zsh fish)'
        '--install[Install completion script]'
        '--path=[Write completion script to path]:file:_files'
    )

    _arguments -C \
        '1: :->command' \
        '*:: :->option'

    case $state in
        command)
            _describe -t commands 'DevSynth commands' commands
            ;;
        option)
            case $words[1] in
                init)
                    _arguments -s : $init_opts
                    ;;
                spec)
                    _arguments -s : $spec_opts
                    ;;
                test)
                    _arguments -s : $test_opts
                    ;;
                code)
                    _arguments -s : $code_opts
                    ;;
                run-pipeline)
                    _arguments -s : $run_opts
                    ;;
                config)
                    _arguments -s : $config_opts
                    ;;
                gather)
                    _arguments -s : $gather_opts
                    ;;
                refactor)
                    _arguments -s : $refactor_opts
                    ;;
                inspect)
                    _arguments -s : $inspect_opts
                    ;;
                webapp)
                    _arguments -s : $webapp_opts
                    ;;
                serve)
                    _arguments -s : $serve_opts
                    ;;
                dbschema)
                    _arguments -s : $dbschema_opts
                    ;;
                doctor)
                    _arguments -s : $doctor_opts
                    ;;
                completion)
                    _arguments -s : $completion_opts
                    ;;
                help)
                    _describe -t commands 'DevSynth commands' commands
                    ;;
            esac
            ;;
    esac
}

_devsynth "$@"
