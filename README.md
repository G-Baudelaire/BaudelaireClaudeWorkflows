# BaudelaireClaudeWorkflows

My Claude Code plugins and workflow files, kept in one place so I can reinstall them on any machine.

## Contents

| Path | What it is |
| --- | --- |
| `plugins/tutor` | The tutor plugin (based on [amosblomqvist/learn](https://github.com/amosblomqvist/learn)): graded quizzes, researcher, PDF reader, session logging. |
| `plugins/programming-coach` | `/programming-coach:coach` turns on coaching mode (questions and hints, no written solutions) for LeetCode-style practice or any learning project. |
| `.claude-plugin/marketplace.json` | Makes this repo installable as a plugin marketplace. |

## Install the plugins

```
/plugin marketplace add G-Baudelaire/BaudelaireClaudeWorkflows
/plugin install tutor@baudelaire-workflows
/plugin install programming-coach@baudelaire-workflows
```

## Coaching mode

Type `/programming-coach:coach` at the start of a practice or learning session. It stays on until you say "stop coaching".

## How this repo is set up

This repo lives in `~/.claude` itself. `.gitignore` ignores everything by default and re-includes only my own plugins and skills, so credentials, history and sessions can never be committed by accident. To track something new, add a `!` exception to `.gitignore` first.
