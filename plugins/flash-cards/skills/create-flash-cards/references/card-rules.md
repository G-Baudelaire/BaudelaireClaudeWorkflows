# The 8 Rules of Good Flashcard Design

Each rule below has the principle, the failure mode, and the rewrite pattern to apply when a card breaks it.

## Contents

1. One fact per card (atomic cards)
2. Use cloze deletions for complex material
3. Avoid context-dependence
4. Add context, not just definitions
5. Write both sides when creating the card
6. Keep the front short — one clear question
7. Include examples on the back
8. Avoid orphan cards — link related concepts
9. Applying the rules together
10. Rewrite patterns quick reference

---

## 1. One fact per card — atomic cards

Each card tests exactly one thing. "The mechanism, side effects, and contraindications of metformin" is three cards, not one.

**Bad — compound card**

> Q: What is metformin's mechanism, main side effect, and why is it contraindicated in renal failure?

**Good — atomic card**

> Q: What is metformin's primary mechanism of action?
> A: Inhibits hepatic gluconeogenesis via AMPK activation

Compound cards fail in a specific way: you recall two of the three parts, mark yourself correct, and the third part never gets learnt. Grading is all-or-nothing, so a card is only as good as its weakest component.

**Rewrite pattern:** one card per part, and if the parts share setup, repeat the setup on each front rather than making one card carry all of them.

**Not a violation:** a back that gives one answer plus context or an example (see rules 4 and 7). One thing to *recall*, not one sentence.

## 2. Use cloze deletions for complex material

Cloze deletions (fill-in-the-blank) beat Q&A for dense factual material. They preserve context while still requiring active retrieval.

> The Krebs cycle produces [2 ATP] per glucose, while oxidative phosphorylation produces [32–34 ATP].

Each blank becomes a separate card, and the surrounding sentence triggers the right memory. In Anki this is `{{c1::2 ATP}}` and `{{c2::32–34 ATP}}` on a Cloze note type — see `anki-format.md`.

Cloze earns its place when the context around the blank is doing work: parameter lists, ordered steps, numeric comparisons, syntax skeletons, definitions where the sentence frame matters. It is the wrong choice when the sentence has exactly one blankable thing and no supporting context — that is a Q&A card wearing a costume.

## 3. Avoid context-dependence

A card that only makes sense next to your notes is useless at recall time. Write cards a stranger could answer.

**Bad**

> Q: What does figure 3.2 show about the pathway?

**Good**

> Q: In the glycolysis pathway, which enzyme catalyses the rate-limiting step?

Watch for: "the figure/diagram/table above", "as discussed in lecture 4", "this algorithm" with no antecedent, "the example" — anything whose referent lives outside the card. Pronouns without antecedents are the most common form, and the easiest to miss because the card was clear the day it was written.

**Rewrite pattern:** name the thing. If the card genuinely needs the diagram, embed the image in the card instead of pointing at one.

## 4. Add context, not just definitions

"Q: What is apoptosis? A: Programmed cell death" is a dictionary entry, not a flashcard. Add why it matters, what triggers it, what happens when it fails.

**Better**

> Q: Why is defective apoptosis central to cancer pathogenesis?
> A: Cancer cells evade programmed death signals, allowing uncontrolled proliferation. Bcl-2 overexpression is a classic mechanism.

Definition cards produce recognition rather than understanding: you can recite the phrase and still not use the concept. Asking *why*, *when*, or *what breaks if* forces the connection that makes the fact retrievable in a real situation.

Some definitions are worth keeping as-is — vocabulary, acronyms, notation, anything where the mapping between symbol and meaning genuinely is the whole fact. Don't inflate "What does SQL stand for?" into an essay. The rule targets *concepts* dressed up as definitions.

## 5. Write both sides when creating the card

Never leave the back vague ("it's complicated", "see notes", "roughly the same as X"). If you can't write a clear back, you don't understand it yet — which is useful information. Fix the understanding, then write the card.

**Rewrite pattern:** when auditing someone else's deck and the back is empty or hand-wavy, either write the real answer (if you can verify it) or flag it to the user as an open question. Don't quietly invent a plausible-sounding back for a fact you can't confirm.

## 6. Keep the front short — one clear question

The front should take under 5 seconds to read. Rambling stems cost time on every single review and blunt the retrieval effect.

Rule of thumb: **more than 2 lines on the front usually means 2 questions.** Conditions, qualifiers, and worked setup belong on the back — except the setup a question is meaningless without, which stays.

**Bad**

> Q: How can you sort queried values by a specific column? Extra 1: how do you do it ascending/descending? Extra 2: how do you add multiple ordering criteria?

**Good** (three cards)

> Q: Which clause sorts query results by a column?
> Q: How do you sort descending rather than ascending in SQL?
> Q: How do you sort by two columns with different directions?

Note how "Extra 1 / Extra 2" is a tell: the author already knew they had three questions and stapled them together.

## 7. Include examples on the back

Abstract rules stay abstract. A concrete example anchors the rule and makes it retrievable under pressure.

> Back: Adverse drug reaction via type IV hypersensitivity (T-cell mediated). Example: contact dermatitis from nickel, tuberculin skin test reaction.

For technical material the example is usually a two-to-four-line code snippet — the smallest snippet that shows the idea working, not a full program. One good example beats three.

Cards that don't need one: pure recall of a term, a number, or a name where the answer *is* the example.

## 8. Avoid orphan cards — link related concepts

An orphan tests a fact in isolation, so it stays disconnected from everything around it. Link cards by tagging them, using hierarchical decks, or referencing related concepts in the card text. A card about ACE inhibitors should sit near the renin-angiotensin-aldosterone system, not float alone.

In practice, three mechanisms:

- **Hierarchical tags** — `pharm::cardio::ace-inhibitors`. Cheap, applies to every card, makes filtered decks possible.
- **In-card references** — a line on the back: "Contrast with ARBs, which block the receptor instead." This is the strongest link because it fires during review.
- **Contrast cards** — an explicit card for the distinction between two things people confuse. Often the highest-value card in a set.

## 9. Applying the rules together

The rules pull against each other and that is fine — knowing which one wins is the skill:

- **1 vs 4/7**: atomicity governs the *front* (one thing asked). Context and examples live on the *back* and don't break atomicity.
- **6 vs 3**: shortening a front must not strand a pronoun. Cut words, not the referent.
- **2 vs 1**: a cloze with four blanks is four cards, so it satisfies atomicity as long as each blank is independently answerable from the surrounding text.

When a card can't satisfy all of them at once, the ordering that usually produces the best deck: answerable at all (3, 5) → tests one thing (1, 6) → worth remembering (4, 7) → findable later (8).

## 10. Rewrite patterns quick reference

| Symptom | Rule | Fix |
|---|---|---|
| Front asks two things, or contains "and"/"Extra 1:"/a numbered list | 1, 6 | Split into N cards, repeating shared setup |
| Front longer than ~2 lines | 6 | Move qualifiers to back; check for a hidden second question |
| Back is one bare phrase for a conceptual question | 4 | Add why it matters / when it applies |
| Back states a rule with no instance | 7 | Add smallest concrete example or snippet |
| "the figure", "above", "this", "in lecture N" | 3 | Name the referent, or embed the image |
| Back empty, vague, or "it depends" | 5 | Write the real answer, or flag to the user |
| Dense list, sequence, or syntax skeleton as Q&A | 2 | Convert to cloze, one blank per element |
| No tags, no links to neighbours | 8 | Hierarchical tag + in-card reference to related concept |
| Two cards with near-identical fronts | 1 | Merge, or sharpen so each tests a distinct thing |
