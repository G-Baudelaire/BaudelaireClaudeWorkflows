// Pure formatting for md-log: turns conversation rows into Obsidian callouts.
// No engine calls here, so it can be unit tested on its own.

import { QUIZ_TOOL_NAME, loggedCalls, type Outcome } from './quiz-logic'

export type Block = { type: string; [field: string]: unknown }
export type Role = 'user' | 'assistant'

export const QA_TOOL = 'AskUserQuestion'

export function callout(type: string, title: string, bodyLines: string[]): string {
  const lines = [`> [!${type}] ${title}`]
  for (const line of bodyLines) lines.push(line.length === 0 ? '>' : `> ${line}`)
  return lines.join('\n')
}

export const userBlock = (text: string): string => `> [!quote] YOU\n\n${text}`
export const assistantBlock = (text: string): string => `> [!abstract] CLAUDE\n\n${text}`

// Text the engine injects around the person's words: reminders, slash-command
// echoes. It is context, not prose, so the log leaves it out.
const NOISE = [
  /<system-reminder>[\s\S]*?<\/system-reminder>/g,
  /<local-command-caveat>[\s\S]*?<\/local-command-caveat>/g,
  /<local-command-stdout>[\s\S]*?<\/local-command-stdout>/g,
  /<command-name>[\s\S]*?<\/command-name>/g,
  /<command-message>[\s\S]*?<\/command-message>/g,
  /<command-args>[\s\S]*?<\/command-args>/g,
]

export function stripNoise(text: string): string {
  let out = text
  for (const pattern of NOISE) out = out.replace(pattern, '')
  return out.trim()
}

function textOf(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content
      .map(part => (part && typeof part === 'object' && 'text' in part ? String((part as { text: unknown }).text) : ''))
      .filter(part => part.length > 0)
      .join('\n')
  }
  return ''
}

function textBlocks(content: Block[]): string[] {
  return content
    .filter(block => block.type === 'text')
    .map(block => String(block.text ?? '').trim())
    .filter(text => text.length > 0)
}

type AskQuestion = { question?: unknown; header?: unknown; options?: unknown; multiSelect?: unknown }

// One [!question] callout per question. The tool call carries only the question
// and its options, never an answer key, so nothing here can leak a correct answer.
export function questionCallouts(input: unknown): string[] {
  const questions = (input as { questions?: unknown })?.questions
  if (!Array.isArray(questions)) return []
  return questions.map((raw: AskQuestion) => {
    const body: string[] = String(raw.question ?? '').split('\n')
    const options = Array.isArray(raw.options) ? raw.options : []
    if (options.length > 0) {
      body.push('')
      options.forEach((option, i) => {
        const label = String((option as { label?: unknown })?.label ?? '')
        body.push(`${i + 1}. ${label}`)
      })
    }
    if (raw.multiSelect === true) body.push('', '(select all that apply)')
    const title = raw.header ? `Question — ${String(raw.header)}` : 'Question'
    return callout('question', title, body)
  })
}

// AskUserQuestion answers come back as: `... answered your questions: "q"="a", "q2"="a2". You can now ...`.
// Pull the pairs out so each question and its answer sit on their own line.
function answerPairs(text: string): string[] {
  const pairs = [...text.matchAll(/"([^"]*)"="([^"]*)"/g)]
  return pairs.map(([, question, answer]) => `**${question}** → ${answer}`)
}

export function answerCallout(result: Block): string {
  const text = stripNoise(textOf(result.content))
  if (result.is_error === true) return callout('warning', 'Question — cancelled', [text || '(no answer)'])
  const pairs = answerPairs(text)
  const body = pairs.length > 0 ? pairs : (text || '(no answer)').split('\n')
  return callout('example', 'Answer', body)
}

const numbered = (all: string[], picked: string[]): string =>
  picked.map(label => `${all.indexOf(label) + 1}. ${label}`).join(', ')

// Quiz questions and verdicts, logged together once the learner has answered.
// The question lists the options in the order the learner saw them. The answer
// key and explanation appear only in the verdict, after the answer.
// The question as asked, with the options in the order the learner sees them.
// Written before the learner answers, so it never holds the key or explanation.
export function quizQuestionCallout(q: { question: string; shown: string[]; multiSelect: boolean }): string {
  const body = q.question.split('\n')
  body.push('', ...q.shown.map((option, i) => `${i + 1}. ${option}`))
  if (q.multiSelect) body.push('', '(select all that apply)')
  return callout('question', 'Quiz', body)
}

// The verdict, written once the learner has answered: the key and explanation appear here.
export function quizVerdictCallout(o: Outcome): string {
  const verdict: string[] = []
  if (o.kind === 'graded') verdict.push(`Your answer: ${numbered(o.shown, o.selected)}`)
  else if (o.kind === 'dontKnow') verdict.push("Your answer: I don't know")
  verdict.push(`Correct answer: ${numbered(o.shown, o.correct)}`)
  if (o.note) verdict.push('', ...`Note: ${o.note}`.split('\n'))
  verdict.push('', ...o.explanation.split('\n'))

  if (o.kind === 'graded' && o.isCorrect) return callout('success', 'Quiz — correct ✓', verdict)
  if (o.kind === 'graded') return callout('failure', 'Quiz — incorrect ✗', verdict)
  if (o.kind === 'dontKnow') return callout('question', "Quiz — I don't know", verdict)
  if (o.kind === 'noAttempt') return callout('warning', 'Quiz — no option chosen', verdict)
  return callout('warning', 'Quiz — dismissed', ['(user skipped)'])
}

// A whole quiz call, written after the fact (backfill, or a quiz asked before
// the note was linked): every question followed by its verdict.
export function quizCallouts(outcomes: Outcome[]): string[] {
  return outcomes.flatMap(o => [quizQuestionCallout(o), quizVerdictCallout(o)])
}

// Renders one conversation row. `names` maps tool_use ids to tool names so a
// later tool_result can be recognised; `hintTool` is the name the engine gives
// for a result row when the tool_use was never seen (e.g. logging started late).
// `quizOutcomes` holds what each quiz call showed and how it was answered.
export function renderRow(
  role: Role,
  content: Block[],
  names: Map<string, string>,
  hintTool?: string,
  quizOutcomes?: Map<string, Outcome[]>,
): string[] {
  const out: string[] = []

  if (role === 'assistant') {
    const texts = textBlocks(content)
    if (texts.length > 0) out.push(assistantBlock(texts.join('\n\n')))
    for (const block of content) {
      if (block.type !== 'tool_use') continue
      names.set(String(block.id), String(block.name))
      if (block.name === QA_TOOL) out.push(...questionCallouts(block.input))
    }
    return out
  }

  const prose = stripNoise(textBlocks(content).join('\n'))
  if (prose.length > 0) out.push(userBlock(prose))
  for (const block of content) {
    if (block.type !== 'tool_result') continue
    const id = String(block.tool_use_id)
    // A rejected call (bad input) is harness noise, not part of the lesson; the retry is what gets logged.
    if (textOf(block.content).includes('<tool_use_error>')) continue
    const name = names.get(id) ?? hintTool
    if (name === QA_TOOL) out.push(answerCallout(block))
    else if (name === QUIZ_TOOL_NAME) {
      if (loggedCalls.has(id)) continue // the quiz tool already wrote it, live
      const outcomes = quizOutcomes?.get(id)
      if (outcomes) out.push(...quizCallouts(outcomes))
      else {
        // A quiz from before logging started (or before a reload): only the
        // model's result text survives. It is written after the answer, so no leak.
        const text = stripNoise(textOf(block.content))
        if (text) out.push(callout('note', 'Quiz (earlier)', text.split('\n')))
      }
    }
  }
  return out
}

// Joins finished blocks onto what the file already holds.
export function appendBlocks(current: string, blocks: string[]): string {
  if (blocks.length === 0) return current
  const prefix = current.trim().length > 0 ? '\n\n' : ''
  return current + prefix + blocks.join('\n\n') + '\n'
}
