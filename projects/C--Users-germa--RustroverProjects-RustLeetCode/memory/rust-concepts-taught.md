---
name: rust-concepts-taught
description: Track Rust concepts that have been taught in this repo
metadata: 
  node_type: memory
  type: project
  originSessionId: 72a4e659-c9df-4ae0-9df4-05a89fa0fe0b
  modified: 2026-08-15T11:28:48.699Z
---

**Concepts introduced:**

1. **`usize`** — Rust's type for array indices and sizes (equivalent to C++'s `size_t`)
2. **`.enumerate()`** — Iterator adapter that pairs elements with their indices as `(usize, &T)`
3. **Borrowing in pattern matching** — `&num` extracts values from iterator without taking ownership
4. **`Option<T>`** — Enum representing "value or nothing" with variants `Some(value)` and `None`
5. **`if let` pattern matching** — Safely extract values from `Option` without `unwrap()`; skips block if pattern doesn't match
6. **Type casting** — Use `as` keyword to convert between types (e.g., `usize as i32`)
7. **`vec!` macro** — Idiomatic way to construct a `Vec` with initial values; also has a repeat form `vec![value; count]` (e.g., `vec![0u16; 26]`)
8. **`HashMap`** — Hash map from `std::collections` with `.get()` returning `Option<&V>`
9. **Implicit returns** — Last expression in a function is returned without `return` keyword
10. **`HashSet`** — Set from `std::collections` with `.contains(&v)` (borrow, just checking) and `.insert(v)` (takes ownership, storing)
11. **Borrow vs. own in method signatures** — `contains(&x)` borrows to inspect; `insert(x)` takes ownership to store; distinct from other languages' `push`/`push_mut`-style naming since Rust encodes mutation via `&mut self` in the signature instead
12. **`String` has no default iteration** — must call `.chars()` (Unicode scalars), `.bytes()` (raw `u8`), etc. explicitly; unlike Python's implicit `for c in string`
13. **Numeric literal type suffixes** — e.g. `0u16`, `1i32` attach a type directly to a literal instead of a separate annotation
14. **`std::iter::zip()` / `.zip()`** — walks two iterators in lockstep, yielding paired tuples; stops at the shorter iterator
15. **`.all()` / `.any()`** — iterator adapters that test a predicate across all/any elements, short-circuiting on the first failing/passing case respectively
