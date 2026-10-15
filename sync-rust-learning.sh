#!/bin/sh
# Copies the Rust project's CLAUDE.md into this repo so it can be committed.
# The memory files are tracked in place (see .gitignore), so they need no copying.
cp "$HOME/RustroverProjects/RustLeetCode/CLAUDE.md" "$HOME/.claude/rust-learning/CLAUDE.md"
cd "$HOME/.claude" && git status --short rust-learning projects
