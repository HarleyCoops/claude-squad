# Claude Squad [![CI](https://github.com/smtg-ai/claude-squad/actions/workflows/build.yml/badge.svg)](https://github.com/smtg-ai/claude-squad/actions/workflows/build.yml) [![GitHub Release](https://img.shields.io/github/v/release/smtg-ai/claude-squad)](https://github.com/smtg-ai/claude-squad/releases/latest)

Claude Squad is a terminal app that manages multiple [Claude Code](https://github.com/anthropics/claude-code), [Codex](https://github.com/openai/codex) (and other local agents including Aider) in separate workspaces, allowing you to work on multiple tasks simultaneously.

![Claude Squad Screenshot](assets/screenshot.png)

### Highlights
- Complete tasks in the background (including yolo / auto-accept mode!)
- Manage instances and tasks in one terminal window
- Review changes before applying them, checkout changes before pushing them
- Each task gets its own isolated git workspace, so no conflicts

<br />

https://github.com/user-attachments/assets/aef18253-e58f-4525-9032-f5a3d66c975a

<br />

### Installation

The easiest way to install `claude-squad` is by running the following command:

```bash
curl -fsSL https://raw.githubusercontent.com/stmg-ai/claude-squad/main/install.sh | bash
```

This will install the `cs` binary to `~/.local/bin` and add it to your PATH. To install with a different name, use the `--name` flag:

```bash
curl -fsSL https://raw.githubusercontent.com/stmg-ai/claude-squad/main/install.sh | bash -s -- --name <name>
```

Alternatively, you can also install `claude-squad` by building from source or installing a [pre-built binary](https://github.com/smtg-ai/claude-squad/releases).

### Prerequisites

- [tmux](https://github.com/tmux/tmux/wiki/Installing)
- [gh](https://cli.github.com/)

### Usage

```
Usage:
  cs [flags]
  cs [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  debug       Print debug information like config paths
  help        Help about any command
  reset       Reset all stored instances
  version     Print the version number of claude-squad

Flags:
  -y, --autoyes          [experimental] If enabled, all instances will automatically accept prompts for claude code & aider
  -h, --help             help for claude-squad
  -p, --program string   Program to run in new instances (e.g. 'aider --model ollama_chat/gemma3:1b')
```

Run the application with:

```bash
cs
```

<br />

<b>To use Claude Squad with Codex or another AI assistant:</b>
1. Set your OpenAI API key in your environment: `export OPENAI_API_KEY=<key>`
2. Run `cs -p "codex"` or `cs -p "aider"` or modify your config file (path can be found by running `cs debug`).

<br />

#### Menu
The menu at the bottom of the screen shows available commands: 

##### Instance/Session Management
- `n` - Create a new session
- `N` - Create a new session with a prompt
- `D` - Kill (delete) the selected session
- `↑/j`, `↓/k` - Navigate between sessions

##### Actions
- `↵/o` - Attach to the selected session to reprompt
- `ctrl-q` - Detach from session
- `s` - Commit and push branch to github
- `c` - Checkout. Commits changes and pauses the session
- `r` - Resume a paused session
- `?` - Show help menu

##### Navigation
- `tab` - Switch between preview tab and diff tab
- `q` - Quit the application
- `shift-↓/↑` - scroll in diff view

### How It Works

1. **tmux** to create isolated terminal sessions for each agent
2. **git worktrees** to isolate codebases so each session works on its own branch
3. A simple TUI interface for easy navigation and management

### License

[AGPL-3.0](LICENSE.md)
