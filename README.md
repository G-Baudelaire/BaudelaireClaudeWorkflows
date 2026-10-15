# BaudelaireClaudeWorkflows

My Claude Code plugins and workflow files, kept in one place so I can reinstall them on any machine.

## Contents

| Path | What it is |
| --- | --- |
| `plugins/tutor` | The tutor plugin (based on [amosblomqvist/learn](https://github.com/amosblomqvist/learn)): graded quizzes, researcher, PDF reader, session logging. |
| `rust-learning/CLAUDE.md` | Project instructions for my Rust LeetCode practice repo. Copy to the root of that project. |
| `rust-learning/memory/` | Claude's saved memories for that project (teaching approach, concepts covered). |
| `.claude-plugin/marketplace.json` | Makes this repo installable as a plugin marketplace. |

## Install the plugins

```
/plugin marketplace add G-Baudelaire/BaudelaireClaudeWorkflows
/plugin install tutor@baudelaire-workflows
```

## Restore the Rust project files

1. Copy `rust-learning/CLAUDE.md` into the project root.
2. Copy `rust-learning/memory/*.md` into `~/.claude/projects/<project-folder-name>/memory/`.

## Not stored here

- Anthropic's synced skills (pdf, docx, pptx, xlsx and so on) are managed by claude.ai and come back on their own when you sign in.
- Credentials, history and session data in `~/.claude` are deliberately left out.
