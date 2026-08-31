"""Shell completion generator for Smart Agent Wiki.

This module generates shell completion scripts for bash, zsh, and fish.

Usage:
    saw completion bash
    saw completion zsh
    saw completion fish
"""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


# Completion templates
BASH_COMPLETION = '''# Bash completion for Smart Agent Wiki
# Install: source ~/.saw/completion.bash
# Or add to ~/.bashrc: source ~/.saw/completion.bash

_saw_completion() {
    local cur prev words cword
    _init_completion || return

    # Main commands
    local commands="init ingest ingest-media query search status web verify lint review audit conflicts freshness mcp tutorial config completion feed docs preview"

    # Short aliases
    local aliases="i q s w v l r a c f"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands} ${aliases}" -- "${cur}"))
        return
    fi

    # Subcommand-specific completions
    case "${words[1]}" in
        ingest|i)
            # File completion
            COMPREPLY=($(compgen -f -- "${cur}"))
            ;;
        query|q)
            # Query modes
            COMPREPLY=($(compgen -W "direct graph reasoning contrast synthesis" -- "${cur}"))
            ;;
        *)
            ;;
    esac
}

complete -F _saw_completion saw
'''

ZSH_COMPLETION = '''# zsh completion for Smart Agent Wiki
# Install: source ~/.saw/completion.zsh
# Or add to ~/.zshrc: source ~/.saw/completion.zsh

#compdef saw

_saw() {
    local -a commands aliases

    commands=(
        'init:Initialize a new wiki'
        'ingest:Ingest documents into wiki'
        'query:Search the knowledge base'
        'search:Full-text search'
        'status:Show wiki status'
        'web:Launch web UI'
        'verify:Verify claims'
        'lint:Lint wiki pages'
        'review:Review claims'
        'audit:Audit trail'
        'conflicts:Show conflicts'
        'freshness:Check freshness'
        'mcp:MCP server'
        'tutorial:Interactive tutorial'
        'config:Configuration'
        'completion:Generate completions'
    )

    aliases=(
        'i:Short for ingest'
        'q:Short for query'
        's:Short for status'
        'w:Short for web'
        'v:Short for verify'
        'l:Short for lint'
    )

    if [[ $CURRENT -eq 2 ]]; then
        _describe 'command' commands
        _describe 'alias' aliases
        return
    fi

    case "${words[2]}" in
        ingest|i)
            _files
            ;;
        query|q)
            _values 'mode' 'direct' 'graph' 'reasoning' 'contrast' 'synthesis'
            ;;
    esac
}

_saw
'''

FISH_COMPLETION = '''# fish completion for Smart Agent Wiki
# Install: source ~/.saw/completion.fish
# Or add to ~/.config/fish/completions/saw.fish

complete -c saw -f

# Main commands
complete -c saw -n __fish_use_subcommand -a init -d 'Initialize a new wiki'
complete -c saw -n __fish_use_subcommand -a ingest -d 'Ingest documents'
complete -c saw -n __fish_use_subcommand -a query -d 'Search knowledge base'
complete -c saw -n __fish_use_subcommand -a search -d 'Full-text search'
complete -c saw -n __fish_use_subcommand -a status -d 'Show wiki status'
complete -c saw -n __fish_use_subcommand -a web -d 'Launch web UI'
complete -c saw -n __fish_use_subcommand -a verify -d 'Verify claims'
complete -c saw -n __fish_use_subcommand -a lint -d 'Lint wiki pages'
complete -c saw -n __fish_use_subcommand -a review -d 'Review claims'
complete -c saw -n __fish_use_subcommand -a audit -d 'Audit trail'
complete -c saw -n __fish_use_subcommand -a tutorial -d 'Interactive tutorial'
complete -c saw -n __fish_use_subcommand -a config -d 'Configuration'

# Short aliases
complete -c saw -n __fish_use_subcommand -a i -d 'Short for ingest'
complete -c saw -n __fish_use_subcommand -a q -d 'Short for query'
complete -c saw -n __fish_use_subcommand -a s -d 'Short for status'
complete -c saw -n __fish_use_subcommand -a w -d 'Short for web'
complete -c saw -n __fish_use_subcommand -a v -d 'Short for verify'

# Subcommand options
complete -c saw -n '__fish_seen_subcommand_from ingest i' -a '(__fish_complete_path)'
complete -c saw -n '__fish_seen_subcommand_from query q' -a 'direct graph reasoning contrast synthesis'
'''


def get_completion_script(shell: str) -> str:
    """Get the completion script for a shell."""
    scripts = {
        "bash": BASH_COMPLETION,
        "zsh": ZSH_COMPLETION,
        "fish": FISH_COMPLETION,
    }
    return scripts.get(shell, "")


def completion(
    shell: str = typer.Argument(
        ...,
        help="Shell type: bash, zsh, or fish",
    ),
    install: bool = typer.Option(
        False,
        "--install", "-i",
        help="Install completion script",
    ),
) -> None:
    """
    Generate shell completion scripts.

    Generate and optionally install shell completion scripts
    for bash, zsh, and fish.

    Examples:
        saw completion bash
        saw completion zsh --install
        saw completion fish
    """
    script = get_completion_script(shell)

    if not script:
        console.print(f"[red]Unknown shell: {shell}[/red]")
        console.print("Supported shells: bash, zsh, fish")
        raise typer.Exit(1)

    if install:
        # Install the completion script
        from pathlib import Path

        install_dir = Path.home() / ".saw"
        install_dir.mkdir(exist_ok=True)

        script_path = install_dir / f"completion.{shell}"
        script_path.write_text(script)

        console.print(f"[green]✓ Completion script installed to {script_path}[/green]")
        console.print("\nTo enable, add to your shell config:")

        if shell == "bash":
            console.print("  echo 'source ~/.saw/completion.bash' >> ~/.bashrc")
        elif shell == "zsh":
            console.print("  echo 'source ~/.saw/completion.zsh' >> ~/.zshrc")
        elif shell == "fish":
            console.print("  echo 'source ~/.saw/completion.fish' >> ~/.config/fish/config.fish")
    else:
        # Just print the script
        console.print(script)


app = typer.Typer(help="Shell completion generation")
app.command(name="completion")(completion)


__all__ = ["completion", "get_completion_script", "BASH_COMPLETION", "ZSH_COMPLETION", "FISH_COMPLETION"]