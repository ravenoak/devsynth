#!/usr/bin/env bash
# Bash completion script for DevSynth CLI

_devsynth_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    commands="init spec test code run-pipeline config gather inspect refactor webapp serve dbschema doctor completion help"

    # Options for specific commands
    init_opts="--wizard --root --language --goals --memory-backend --offline-mode --features --auto-confirm --defaults --non-interactive --metrics-dashboard"
    spec_opts="--requirements-file --output-file --verbose"
    test_opts="--spec-file --output-file --verbose"
    code_opts="--test-file --output-dir --language --verbose"
    run_opts="--target --verbose"
    config_opts="--key --value --list --verbose"
    gather_opts="--interactive --output-file --verbose"
    refactor_opts="--file --verbose"
    inspect_opts="--file --verbose"
    webapp_opts="--framework --output-dir --verbose"
    serve_opts="--host --port --verbose"
    dbschema_opts="--input-file --output-file --verbose"
    doctor_opts="--fix --verbose"
    completion_opts="--shell --install --output"

    # Handle command-specific options
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        # Completing the command
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return 0
    fi

    # Handle options for specific commands
    case "${COMP_WORDS[1]}" in
        init)
            COMPREPLY=( $(compgen -W "${init_opts}" -- "${cur}") )
            ;;
        spec)
            COMPREPLY=( $(compgen -W "${spec_opts}" -- "${cur}") )
            ;;
        test)
            COMPREPLY=( $(compgen -W "${test_opts}" -- "${cur}") )
            ;;
        code)
            COMPREPLY=( $(compgen -W "${code_opts}" -- "${cur}") )
            ;;
        run)
            COMPREPLY=( $(compgen -W "${run_opts}" -- "${cur}") )
            ;;
        config)
            COMPREPLY=( $(compgen -W "${config_opts}" -- "${cur}") )
            ;;
        gather)
            COMPREPLY=( $(compgen -W "${gather_opts}" -- "${cur}") )
            ;;
        refactor)
            COMPREPLY=( $(compgen -W "${refactor_opts}" -- "${cur}") )
            ;;
        inspect)
            COMPREPLY=( $(compgen -W "${inspect_opts}" -- "${cur}") )
            ;;
        webapp)
            COMPREPLY=( $(compgen -W "${webapp_opts}" -- "${cur}") )
            ;;
        serve)
            COMPREPLY=( $(compgen -W "${serve_opts}" -- "${cur}") )
            ;;
        dbschema)
            COMPREPLY=( $(compgen -W "${dbschema_opts}" -- "${cur}") )
            ;;
        doctor)
            COMPREPLY=( $(compgen -W "${doctor_opts}" -- "${cur}") )
            ;;
        completion)
            COMPREPLY=( $(compgen -W "${completion_opts}" -- "${cur}") )
            ;;
        help)
            COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
            ;;
    esac

    # Handle option arguments
    case "${prev}" in
        --path|--root|--output-dir|--output-file|--requirements-file|--spec-file|--test-file|--file|--input-file|--output)
            # File/directory completion
            COMPREPLY=( $(compgen -f -- "${cur}") )
            return 0
            ;;
        --template)
            # Template options
            COMPREPLY=( $(compgen -W "basic advanced webapp api" -- "${cur}") )
            return 0
            ;;
        --language)
            # Language options
            COMPREPLY=( $(compgen -W "python javascript typescript java csharp go rust" -- "${cur}") )
            return 0
            ;;
        --memory-backend)
            # Memory backend options
            COMPREPLY=( $(compgen -W "memory file kuzu chromadb" -- "${cur}") )
            return 0
            ;;
        --framework)
            # Framework options
            COMPREPLY=( $(compgen -W "flask django fastapi express react vue angular" -- "${cur}") )
            return 0
            ;;
        --target)
            # Target options
            COMPREPLY=( $(compgen -W "unit-tests integration-tests all" -- "${cur}") )
            return 0
            ;;
        --key)
            # Config keys
            COMPREPLY=( $(compgen -W "model provider offline_mode memory_backend log_level" -- "${cur}") )
            return 0
            ;;
        --shell)
            # Shell options
            COMPREPLY=( $(compgen -W "bash zsh fish" -- "${cur}") )
            return 0
            ;;
    esac

    return 0
}

complete -F _devsynth_completion devsynth
