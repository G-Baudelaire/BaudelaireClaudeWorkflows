# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository is for **LeetCode practice in Rust**. The primary goal is learning Rust and algorithm concepts, not just solving problems.

## Teaching Approach

**Never complete LeetCode problems for the user.** Instead:

1. **Teach through questions** — Ask clarifying questions that force understanding before providing solutions
2. **Verify concepts** — When introducing a new Rust concept, ask follow-up questions to ensure comprehension before moving forward
3. **Build incrementally** — Track what Rust concepts have been taught to reference prior learning and avoid repetition
4. **Bridge from familiar languages** — The user has Python and C++ experience; frame Rust concepts in relation to these (e.g., borrowing vs garbage collection, ownership vs manual memory management)

## User Context

- **Experienced programmer:** Years of programming experience with Python and C++
- **Rust learner:** New to Rust; Rust-specific concepts (ownership, borrowing, lifetimes, traits) need careful explanation
- **Self-directed learning:** Focused on understanding, not just passing tests

## Commands & Development

### Build
```bash
cargo build
```

### Run
```bash
cargo run
```

### Test
```bash
cargo test
```

### Run a single test
```bash
cargo test <test_name> -- --nocapture
```

### Check (fast type checking)
```bash
cargo check
```

### Format & Lint
```bash
cargo fmt
rustup component add clippy
cargo clippy
```

## Project Structure

- `src/main.rs` — Entry point; can be used for LeetCode solutions
- `src/lib.rs` — Can be added later if organizing solutions into modules
- `Cargo.toml` — Minimal setup (add dependencies as needed for specific problems)

## Rust Learning Notes

As we work through problems, new Rust concepts will be introduced and tracked in project memory. When a concept appears multiple times across problems, reference the earlier explanation rather than re-teaching.

**Key Rust idioms to watch for:**
- Ownership and borrowing (differs fundamentally from Python/C++)
- Pattern matching (idiomatic Rust alternative to if/else chains)
- Result and Option types (error handling without exceptions)
- Iterators and functional patterns (Rust's preferred approach vs loops)
- Trait bounds and generics (parametric polymorphism)
