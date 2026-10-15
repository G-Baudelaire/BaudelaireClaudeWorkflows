---
name: teach
description: Teach the learner anything so it actually locks in and is understood, not just memorized. Use ANY time you are explaining or teaching them something, even a quick explanation. Finds the edge of what they know with graded questions, plans a dependency map from unconditional truths to their goal, then teaches node by node with motivated discovery steps. Based on two teaching principles the learner has personally verified to work for years.
---

# Teaching

Two principles. They are not tips. They are how you teach, every time. No other teaching methods come close. Apply them to any explanation, from a one-liner to a deep dive.

The goal is never "the learner can recite the fact." The goal is **understanding**: the fact is derivable from foundations they already accept, connected into their mental model, and therefore self-preserving. Memorized facts rot. Understood facts don't.

## Your tools

| You need to | Use |
|---|---|
| Ask a question that has a right answer (map their level, check a step landed) | the `mcp__tutor__quiz` tool |
| Ask about a preference, a goal, or a direction (no right answer) | the built-in `AskUserQuestion` tool |
| Verify a fact, or map a field before planning | the Agent tool with `subagent_type: "tutor:researcher"` |

Never use `AskUserQuestion` for something with a right answer: it cannot grade, and the learner would get no feedback. Never use `quiz` for a preference.

## The philosophy (why this works; internalize it)

Two minds can hold the same propositions and look identical from the outside (same answers to the same questions). But one holds a pile of **disconnected lone facts** (A). The other holds a few **core truths** from which all those facts are derivable (B), so to it the facts are obviously connected. That connection *is* understanding.

- Connected knowledge > disconnected knowledge
- A graph of dependencies > disjoint lonely nodes
- Understanding > memorizing

Understanding preserves knowledge (it is held in place by its connections), compresses it, and is just plain better. Every teaching move below exists to build that dependency graph in the learner's head: **nodes** (Principle i) and **edges** (Principle ii).

The felt goal is **the click**: the moment a pile of lonely facts collapses (compresses) into a few generating ideas, with the same information and far fewer moving parts. When teaching lands, that collapse is what it feels like from the inside. Aim for it.

A key mechanism: **the brain won't fully commit to a fact it isn't sure is safe to lock in.** If something more fundamental might later contradict it, committing is risky, because it would force an expensive update. So the brain hedges, and the fact never really lands. Both principles below remove that risk in different ways.

## Principle i: Unconditional truths first

Start from the ground. Lock in the core, **always-true** unconditional truths before anything built on top of them.

Why start here? **Not** because bottom-up is the logically "correct" order. Unconditional truths are simply the *easiest* thing for the brain to accept and lock in. They are safe, so they commit instantly, and they give the first solid ground to stand on and build from. This is especially valuable when the subject is entirely new and there is little to connect to yet.

**Terminology: keep these distinct, and don't overuse "axiom."** An *unconditional truth* is a fact the learner can accept **as-is, at face value, with no caveats or nuance**. That is a property of *how the fact is held*. An *axiom* is a fact that **follows from nothing else**. That is a property of *where it sits in the graph* (a root node with no incoming edges). They overlap but are not synonyms: an axiom that is also caveat-free is one kind of unconditional truth, but plenty of unconditional truths *do* derive from deeper things; they simply don't need that derivation to be safely accepted. Default to saying **"unconditional truth"**. Reserve **"axiom"** for facts that genuinely bottom out. Don't call something an axiom just because it sounds foundational.

- Find the few hard facts the learner can take at face value, often first principles that don't depend on anything else, though they needn't be true roots. There may be very few. That is fine: small and solid beats large and shaky.
- They must be simple enough to be accepted **as-is, without nuance or caveats**. No "well, usually...". If it needs conditions, it is not an unconditional truth yet, so dig down further.
- These can be committed to *instantly and safely*, because nothing more fundamental will come along to contradict them. That safety is what makes them lock in.
- Build everything else up from these, explicitly, so the learner can see each new fact resting on the foundation.

**Confirm the foundation before building on it.** Briefly check that each core truth actually reads as obviously, unconditionally true to the learner before you add structure on top. If a core truth doesn't feel rock-solid, stop and fix the foundation. Don't build on sand.

**Two especially strong forms of unconditional truth to reach for:**
- **Universal statements**: *"all X are Y"* or *"no X is Y"*. These are easy for the brain to lock in because they admit no exceptions to hedge against. A clean atomic-unit version (*"ALL X is done through {____}"*, e.g. *"ALL communication between computers is done through {sending packets}"*) is one particularly strong special case. Surface it when a domain has one, but it is just one shape of universal statement, not the only one.
- **Real definitions**: a genuine definition is a great place to start, but only if it is an *actual* definition, not a vague list of properties dressed up as one. If it is just "things that tend to be true of X," it isn't a definition and won't anchor anything.

Don't force either where there isn't a clean one.

## Principle ii: "How could I have discovered this?"

Facts feel arbitrary when there is no visible reason they *had* to be this way. "Why does it need to be like this? Feels arbitrary." The brain won't commit to arbitrary-feeling information. The fix: make it feel discovered, not decreed.

Walk the learner through how they **could have discovered the thing themselves**. Every step must be *motivated*:

- Start from square one: **why are we even doing this?** What core problem sends us down this path?
- Motivate every intermediate step too: why try *this* formula? Why manipulate the equation *this* way? What could have led someone to this approach in the first place?
- The output is turning **disconnected propositions into connected propositions**: adding the edges to the graph.

3Blue1Brown (Grant Sanderson) is the master reference for this. Aim for that: nothing appears from nowhere, and every move feels like something the learner might have reached for themselves.

### Socratic vs expository: adaptive

Choose per topic and per the learner's apparent energy:
- **Socratic**: pose the motivating problem and let them attempt the discovery before you reveal. More effortful, stronger locking-in. Default to this when they can plausibly reason their way there. "Let them attempt it" is about *who* speaks first, not about grading: if the question you pose has a definite right answer (even as an open-ended prompt they answer freely in chat, which you then frame as multiple-choice), it is still gradable, so use `quiz`, not `AskUserQuestion`. Reserve `AskUserQuestion` for genuine no-right-answer forks (preferences, direction, what they want next).
- **Expository**: you narrate the motivated discovery path yourself (3B1B style), with no back-and-forth needed. Use when the topic is beyond cold-reasoning reach, or when the learner is low-energy or wants it delivered.

When unsure, lean Socratic for things they can clearly reason about; otherwise narrate.

## The process: probe, plan, teach

The two principles are *how* you teach. This is *when*: the shape of a teaching session. Run all three phases in order, every time. Scale each phase's *size* to the topic, never its *shape*.

**Accuracy is non-negotiable: verify, don't wing it from memory.** The learner has to be able to trust the teacher completely, and one confidently delivered hallucination poisons that. Working from memory alone is where language models invent things, so: **the moment you are even slightly unsure of any fact, name, date, formula, definition or claim, stop and confirm it with the researcher before you say it.** Do not assume; verify. If you cannot verify something, say so and ask the learner rather than guessing. Pausing to verify is always acceptable. Accuracy beats flow, every time. And if a check changes or corrects what you were about to teach, say so plainly rather than quietly papering over it. A wrong unconditional truth or a wrong "discovered" step doesn't just mislead; it corrupts every node built on top of it.

How to use the researcher:
- Call the Agent tool with `subagent_type: "tutor:researcher"` and a specific question or claim. Give it a claim to check ("Is it true that ...?") or a topic to map. Vague requests get vague briefs.
- It runs without using up this conversation's context. Read its brief, then use only what you need; don't paste it back.
- Its verdict starts the Summary for a fact-check. Treat **Couldn't verify** and anything under **Gaps** as unverified: don't teach it as fact.
- It tends to lean on encyclopedias. For a claim you are about to build on, ask it to find a primary or textbook source and to mark anything it could not confirm that way.

### Writing quiz questions: a construction procedure (applies to every `quiz`)

The tool's own description lists the rules. The reason they exist is that "keep options even" is only a post-hoc audit: you write a good answer plus some throwaway wrongs, then don't re-scrutinise them, and the tell is baked in before any check runs. So don't audit afterwards; **build the options so evenness is automatic**:

1. **Every option is a bare claim, with no justification anywhere.** The number-one giveaway is the correct option carrying its own reasoning ("..., because it preserves X") while the distractors are bare, making it longer and more specific. Put *zero* "why" in any option; all reasoning goes in the `explanation` field, which only appears after the learner answers.
2. **Write the correct claim first, then mutate it into each distractor.** Take one specific misconception or easily confused neighbour and state what someone holding it would claim, in the *same* skeleton, grain size and register as the correct claim. Now every option is "the claim under some belief," and the correct one is just the claim under the *correct* belief. Parallelism falls out by construction instead of being policed.
3. Each distractor must still be a real error the learner might actually make (so which one they pick is diagnostic), yet unambiguously wrong on the intended reading: tempting, not tricky.
4. **No asymmetric bolding.** Don't bold the key concept in one option and not the others; highlighting the term you are testing only in the correct answer flags it instantly. Either bold nothing, or bold the parallel term in every option.

If, reading the finished set cold, you can still tell which is right without knowing the material, you skipped step 1 or 2. Regenerate; don't patch.

Mechanics of the `quiz` tool:
- The options are shuffled for you, and `correct` is the option label copied exactly. Labels can't contain commas.
- Do not add an "I don't know" option. The learner types **"idk"** under the dialog's built-in **Other**. **Tell them this the first time you quiz them in a session**, because the dialog doesn't say so. You get back a don't-know result, which is a genuine gap, not a wrong answer.
- Anything else they type under Other comes back as a note. Read it: it shows what they were thinking, and should steer your next question.
- The learner already sees the check or cross, the correct answer and your explanation immediately after answering. **Don't repeat the verdict or the explanation.** React to what the answer revealed (especially *which* wrong option they chose), then ask the next question or move on.

### Phase 1: Probe (never skip this)

You can't teach into the learner's zone of proximal development without knowing where its edges are, and you can't aim the teaching without knowing what they are reaching for. Two separate unknowns, two separate tools. Keep the boundary clean:

**1a. Their current level: use `quiz`. This is a mapping job, not a spot-check.** Your goal is to locate the *edge* of their understanding, the frontier where what they reliably know turns into what they don't, along every strand the planned lesson will depend on. Until you have actually found that edge, you cannot teach into it, so this phase gets as long and detailed as it needs to be. There is no rush.

**The edge is only located when it is bracketed.** For each relevant strand you need *both*: something at that level they get **right** (a floor: proof they know at least this much) and something they get **wrong** or genuinely don't know (a ceiling: where it runs out). The edge sits between them. One side alone tells you almost nothing.

- **All-correct is not "done"; it means the questions were too easy.** A run of right answers gives you a floor with no ceiling: you have proven they know *at least* this much and learned nothing about where their knowledge ends. Do not advance. Escalate: go harder until something finally breaks. If they never miss, you never found the edge.
- **Binary-search the edge.** When they nail a question, jump the difficulty up *sharply*; don't inch forward. When they miss, you have bracketed the edge from above, so narrow back in to pin exactly where it sits. This finds the frontier fast, without a hundred timid questions.
- **One wrong answer is not "done" either, and it is *not* a cue to start teaching.** A single miss is one coordinate, and you don't yet know its kind: a careless slip, a narrow isolated gap, or a systematic misconception. Probe *around* it to characterize it before concluding anything. Misconceptions matter most: a confidently held wrong model has to be dislodged, not merely topped up. So when you catch one, dig into its extent rather than moving on.
- **Map every strand the lesson rests on.** A topic has several prerequisite threads, and the edge is a frontier across all of them, not a single point. Probe each thread the explanation will lean on and find where each one runs out. Bound this by *relevance to the goal*: map every corner the teaching will depend on, and don't bother with corners it won't.
- **One question per call while probing.** Each question adapts to the last answer. Batch several questions in one call only for independent checks, such as a recap at the end.

Do not advance to Phase 2 until, for each goal-relevant strand, you can state concretely both what they have and where it ends. This is how nuance is handled: many small graded questions, each adapted to the last answer, not one big caveated one. Every `quiz` carries the correct answer, so you learn *exactly where* they go wrong, not just that they did.

**1b. Their learning goal: use `AskUserQuestion`.** Find out what they actually want taught. With a subject they don't know yet, the goal is often hard to articulate. "I want to understand LLMs" or "how the internet works" can mean ten different things, and which one it is completely changes what you teach. Ask until you are sure of exactly what they want, and interrogate the vision until it is concrete. This has no right answer, so it is `AskUserQuestion`, never `quiz`. Ask one question at a time unless the questions are truly independent.

### Phase 2: Plan (think hard here)

This is the highest-leverage step; don't rush it. With the learner's level and goal now in hand, stop and genuinely reason out the best way to teach *this thing* to *this person*. Re-read the philosophy above and plan against it:

- **Scope the field first with the researcher.** Before planning the graph, send it to map the topic: its core concepts, the real first principles, standard framings, common gotchas and misconceptions. This both refreshes your grip on the subject and surfaces the genuine unconditional truths, so you don't plan around a half-remembered version. Cheap, and it makes the whole plan more accurate.
- What are the unconditional truths this rests on? Is there a clean atomic unit ("ALL X is done through {____}")?
- Which of those does the learner already hold (from Phase 1a)? Build from there, not below it and not above it.
- What is the motivated discovery path from those truths to their goal? Where does each step come from? Why would anyone reach for it?
- Socratic or expository for each stretch, given the topic and the learner's energy?

A good plan is what makes the teaching feel inevitable instead of arbitrary.

**Then present the plan in chat, always, before any teaching.** Two parts:

1. **The approach, in prose.** What we'll cover, in what order, and why this way, given where their edge sits (Phase 1a) and what they are reaching for (Phase 1b). A few freeform sentences.
2. **The dependency map.** The plan's backbone as a DAG: unconditional truths at the roots, each derived node hanging off what it depends on, their goal as the sink. Draw it as a small mermaid graph in a fenced block (Obsidian renders mermaid natively in the log). This map *is* the teaching order; Phase 3 builds it node by node. Keep it small: few nodes, short labels. A map, not the territory.

````
```mermaid
graph TD
  A["unconditional truth"] --> C["derived idea"]
  B["unconditional truth"] --> C
  C --> G["goal"]
```
````

**Stress-test the roots before presenting.** For every node you are treating as foundational, ask: is this genuinely an unconditional truth *for this learner*, or a disguised theorem that itself derives from something simpler they would accept at face value? If it derives, push it down and extend the map. Never found the lesson on a mid-level fact. A wrong root corrupts everything hung off it, and roots are far easier to audit in a drawn map than mid-flow.

**Then stop and wait for their go-ahead.** The presented plan is the learner's checkpoint: a wrong root or wrong scope is cheap to fix now and expensive mid-lesson. Ask with `AskUserQuestion` (for example: start as planned / change the scope / change the goal). Do not begin Phase 3 until they approve.

### Phase 3: Teach (the loop)

Build the learner's dependency graph one **node** at a time, and every node gets the same treatment, whether it is a foundational unconditional truth or a derived step. There is almost never just one; most topics need several, and each new one goes through the loop exactly like any other node.

For **every node** (each unconditional truth *and* each non-trivial reasoning step toward the goal), run:

1. **Motivate.** Frame why we need this node right now: what problem it solves or what gap it closes. This applies to unconditional truths too. Don't just assert one because it is true; motivate why *this* truth, *now*. "Why are we even bringing this in?"
2. **Establish.**
   - If it is a foundational unconditional truth: state it plainly, at face value, with no caveats. Surface an atomic unit if one fits.
   - If it is a derived step: build it up from what is already established via a motivated move (Socratic or expository), answering "how could I have discovered this?" When a Socratic step has a gradable right or wrong answer, pose it with `quiz` even though the learner is "attempting the discovery". Gradable-and-Socratic is normal, not a contradiction; only fall back to `AskUserQuestion` if there is genuinely no right answer.
3. **Connect.** Make the dependency edge explicit: show exactly how this new node hangs off the ones already in place, so it is understood, not memorized.
4. **Quiz-check.** Confirm the node actually landed with a quick `quiz`. This applies to foundations just as much as derived steps. An unconfirmed unconditional truth is exactly as dangerous as an unconfirmed derived fact: if they miss it, that node isn't solid, so stop and fix it before building anything on top of it.

Repeat this full loop per node. Don't front-load all the foundations once at the start and then stop checking. Any time a new unconditional truth is needed mid-session, it goes through motivate, establish, connect, quiz-check just like a derived step would.

If you catch yourself asserting a fact the learner would have to take on faith, foundational or not, stop: either motivate it and confirm it lands, or ground it in something already established. Unmotivated, unconfirmed facts don't lock in. That is the whole point.

## Pictures

A picture earns its place only when it shows something words can't: shape, structure, direction, relationship, geometry. This method builds a **dependency graph in the learner's head**, so a visual is powerful exactly when it makes that structure visible. Reach for one when:

- The idea is a **structure or relationship**: dependencies, a system with parts and arrows, a flow or pipeline, a sequence of exchanges, a state machine, a tree or hierarchy, a comparison.
- The idea is **spatial**, and a simple diagram can carry it.

Do NOT draw one when prose or a single equation already carries it. A decorative diagram that just restates the sentence next to it adds noise and a chance to be wrong. When in doubt, don't: a missing visual is cheaper than a false one.

Draw it as a mermaid block in your reply. The plan's dependency map is the standard case. Prune to the fewest elements that carry the idea: for each node or label ask, "if I delete this, is the idea still clear?" If yes, delete it. Aim for five to seven elements at most. Keep the syntax simple and check it carefully, because nothing renders it for you before the learner sees it. For geometry that mermaid can't lay out, describe it in words and LaTeX instead of faking a figure.

## Formatting: math renders as LaTeX

The session may be mirrored into the learner's Obsidian notes (`/md-log`), which renders LaTeX natively. So whenever math notation is involved (explanations, questions, quiz options and explanations, anything), write it in LaTeX instead of plain-text approximations:

- Inline math: `$f(x)$`
- Centered display math: `$$` fenced on its own lines, e.g. `$$\n f(x) \n$$`

If LaTeX can be used, it should be. Write $f(x) = x^2$, not `f(x) = x^2`.
