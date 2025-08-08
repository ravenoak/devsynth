# DevSynth Shell Completions

This directory contains shell completion scripts for the DevSynth CLI. These scripts provide tab completion for DevSynth commands and options in various shells.

For additional details on enabling completion in the CLI, see the [CLI UX guide](../../docs/user_guides/cli_ux.md#installing-shell-completion).

## Available Completion Scripts

- `devsynth-completion.bash`: Completion script for Bash
- `devsynth-completion.zsh`: Completion script for Zsh
- `devsynth-completion.fish`: Completion script for Fish

## Installation Instructions

### Bash

#### Temporary Usage

To use the Bash completion script for the current session only:

```bash
source scripts/completions/devsynth-completion.bash
```

#### Permanent Installation

To install the Bash completion script permanently:

1. Copy the completion script to the Bash completion directory:

```bash
# For most Linux distributions
sudo cp scripts/completions/devsynth-completion.bash /etc/bash_completion.d/devsynth

# For macOS with Homebrew
cp scripts/completions/devsynth-completion.bash $(brew --prefix)/etc/bash_completion.d/devsynth
```

2. Alternatively, you can add the following line to your `~/.bashrc` or `~/.bash_profile`:

```bash
source /path/to/devsynth/scripts/completions/devsynth-completion.bash
```

3. Restart your shell or run `source ~/.bashrc` (or `source ~/.bash_profile`) to apply the changes.

### Zsh

#### Temporary Usage

To use the Zsh completion script for the current session only:

```zsh
source scripts/completions/devsynth-completion.zsh
```

#### Permanent Installation

To install the Zsh completion script permanently:

1. Create a directory for custom completions if it doesn't exist:

```zsh
mkdir -p ~/.zsh/completions
```

2. Copy the completion script to the Zsh completions directory:

```zsh
cp scripts/completions/devsynth-completion.zsh ~/.zsh/completions/_devsynth
```

3. Add the completions directory to your `fpath` in `~/.zshrc`:

```zsh
fpath=(~/.zsh/completions $fpath)
autoload -U compinit
compinit
```

4. Restart your shell or run `source ~/.zshrc` to apply the changes.

### Fish

#### Temporary Usage

To use the Fish completion script for the current session only:

```fish
source scripts/completions/devsynth-completion.fish
```

#### Permanent Installation

To install the Fish completion script permanently:

1. Copy the completion script to the Fish completions directory:

```fish
cp scripts/completions/devsynth-completion.fish ~/.config/fish/completions/devsynth.fish
```

2. Fish will automatically load the completions the next time you start a shell.

## Usage

Once installed, you can use tab completion with the DevSynth CLI:

```bash
# Tab completion for commands
devsynth <TAB>

# Tab completion for options
devsynth init <TAB>

# Tab completion for option arguments
devsynth init --template <TAB>
```

## Troubleshooting

### Bash

If completions aren't working in Bash:

1. Make sure Bash completion is installed:
   - On Ubuntu/Debian: `sudo apt-get install bash-completion`
   - On macOS with Homebrew: `brew install bash-completion`

2. Check that the completion script is being sourced correctly:
   ```bash
   echo $BASH_COMPLETION_COMPAT_DIR
   ```

3. Try reloading the completion script:
   ```bash
   source /path/to/devsynth-completion.bash
   ```

### Zsh

If completions aren't working in Zsh:

1. Check that the completion system is initialized:
   ```zsh
   echo $fpath | grep completions
   ```

2. Rebuild the completion cache:
   ```zsh
   rm -f ~/.zcompdump; compinit
   ```

### Fish

If completions aren't working in Fish:

1. Check that the completion script is in the right location:
   ```fish
   ls ~/.config/fish/completions/devsynth.fish
   ```

2. Try reloading the completion script:
   ```fish
   source ~/.config/fish/completions/devsynth.fish
   ```

## Updating Completions

If the DevSynth CLI commands or options change, you'll need to update the completion scripts accordingly. The scripts are designed to be easy to modify:

- In the Bash script, update the `commands` and `*_opts` variables.
- In the Zsh script, update the `commands` array and the `*_opts` arrays.
- In the Fish script, update the `commands` and `*_opts` variables.

After updating, reinstall the completion scripts as described above.
