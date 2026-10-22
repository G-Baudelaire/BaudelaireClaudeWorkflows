# Flashcard lint report

- notes: **12**
- notes with no mechanical flags: **2** (16%)
- distinct issue types: **14**

Flags indicate shape, not correctness. Read each flagged card before changing it.

## Issues by type

| Rule | Issue | Cards |
|---|---|---|
| 4 | `thin_back` | 3 |
| 2 | `broken_cloze` | 3 |
| 8 | `untagged` | 2 |
| 5 | `vague_back` | 2 |
| 5 | `empty_front` | 1 |
| 1 | `multi_question` | 1 |
| 6 | `long_front` | 1 |
| 1 | `list_front` | 1 |
| 7 | `no_example` | 1 |
| 3 | `context_dependent` | 1 |
| 3 | `dangling_pronoun` | 1 |
| - | `field_count` | 1 |
| 1 | `stapled_front` | 1 |
| 1 | `duplicate_front` | 1 |

### `thin_back` (rule 4) — 3 card(s)

- **#2** What is a join? And what is a key? — _1 words, conceptual question_
- **#3** What is the difference between a clustered and a non clustered index and how doe — _2 words, conceptual question_
- **#5** What is normalisation? — _2 words, conceptual question_

### `broken_cloze` (rule 2) — 3 card(s)

- **#8** {{c1::물 means water — _unbalanced cloze braces_
- **#9** {{ broken }} {{c — _unbalanced cloze braces_
- **#9** {{ broken }} {{c — _cloze braces without a c-number_

### `untagged` (rule 8) — 2 card(s)

- **#1**  — _no topical tag_
- **#3** What is the difference between a clustered and a non clustered index and how doe — _no topical tag_

### `vague_back` (rule 5) — 2 card(s)

- **#2** What is a join? And what is a key? — _back reads as a placeholder: 'TBD'_
- **#3** What is the difference between a clustered and a non clustered index and how doe — _back reads as a placeholder: 'it depends'_

### `empty_front` (rule 5) — 1 card(s)

- **#1**  — _note has no first field_

### `multi_question` (rule 1) — 1 card(s)

- **#2** What is a join? And what is a key? — _2 question marks on the front_

### `long_front` (rule 6) — 1 card(s)

- **#3** What is the difference between a clustered and a non clustered index and how doe — _128 chars / 24 words_

### `list_front` (rule 1) — 1 card(s)

- **#4** Name three join types — _asks for a list — consider cloze or one card per item_

### `no_example` (rule 7) — 1 card(s)

- **#6** Explain how an index speeds up lookups — _explanatory card with no example on the back_

### `context_dependent` (rule 3) — 1 card(s)

- **#7** This is shown in figure 3 — _refers to material outside the card_

### `dangling_pronoun` (rule 3) — 1 card(s)

- **#7** This is shown in figure 3 — _front opens with an unanchored pronoun_

### `field_count` (rule -) — 1 card(s)

- **#8** {{c1::물 means water — _3 fields, deck uses 2_

### `stapled_front` (rule 1) — 1 card(s)

- **#10** Part 1: what? Extra 2 — _front bundles numbered sub-questions_

### `duplicate_front` (rule 1) — 1 card(s)

- **#0** 사과 — _also at note(s) [11]_
