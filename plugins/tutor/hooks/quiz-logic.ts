// Pure quiz logic: validation, shuffling, answer parsing, grading, and the text
// that goes back to the model and to the learner. No engine calls here, so it
// can be unit tested on its own.

export const QUIZ_TOOL_NAME = 'mcp__tutor__quiz'

export type QuizQuestion = {
  question: string
  options: string[]
  // One label, or several for a multi-select question. A model sometimes sends
  // a list as a JSON string, which correctList() undoes.
  correct: string | string[]
  explanation: string
  multiSelect?: boolean
  shuffle?: boolean
  header?: string
}

export type QuizInput = { questions: QuizQuestion[] }

export type OutcomeKind = 'graded' | 'dontKnow' | 'noAttempt' | 'dismissed'

export type Outcome = {
  kind: OutcomeKind
  question: string
  shown: string[] // options in the order the learner saw them
  multiSelect: boolean
  correct: string[]
  explanation: string
  selected: string[]
  isCorrect?: boolean // only when kind is 'graded'
  note?: string
}

// Outcomes by tool_use id, so md-log can log what the learner actually saw.
export const outcomesByCall = new Map<string, Outcome[]>()

// Quiz calls whose questions and verdicts the quiz tool already wrote to the
// linked note as they happened, so md-log must not write them again.
export const loggedCalls = new Set<string>()

// "I don't know" is typed under the dialog's built-in "Other".
const DONT_KNOW = /^(idk|i\s*don['’]?t\s*know|don['’]?t\s*know|dunno|not\s*sure)[.!]?$/i

export const looksLikeDontKnow = (text: string): boolean => DONT_KNOW.test(text.trim())

export function correctList(q: Pick<QuizQuestion, 'correct'>): string[] {
  const raw = q.correct
  if (Array.isArray(raw)) return raw.map(String)
  if (typeof raw === 'string') {
    const trimmed = raw.trim()
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      try {
        const parsed: unknown = JSON.parse(trimmed)
        if (Array.isArray(parsed)) return parsed.map(String)
      } catch {
        // not JSON: a single label that happens to start with a bracket
      }
    }
    return [raw]
  }
  return []
}

// Returns a reason the call is malformed, or undefined when it is fine.
export function validate(input: QuizInput): string | undefined {
  const questions = input?.questions
  if (!Array.isArray(questions) || questions.length < 1 || questions.length > 4) {
    return 'quiz needs 1 to 4 questions'
  }
  for (const [i, q] of questions.entries()) {
    const at = `quiz question ${i + 1}`
    if (typeof q?.question !== 'string' || q.question.trim() === '') return `${at} needs question text`
    if (typeof q.explanation !== 'string' || q.explanation.trim() === '') return `${at} needs an explanation`
    const options = q.options
    if (!Array.isArray(options) || options.length < 2 || options.length > 4) return `${at} needs 2 to 4 options`
    if (options.some(option => typeof option !== 'string' || option.trim() === '')) {
      return `${at} options must be non-empty text`
    }
    if (new Set(options).size !== options.length) return `${at} options must be distinct`
    if (options.some(option => option.includes(','))) return `${at} option labels cannot contain commas`
    const correct = correctList(q)
    if (correct.length === 0) return `${at} needs a correct answer`
    if (new Set(correct).size !== correct.length) return `${at} correct answers must be distinct`
    for (const label of correct) {
      if (!options.includes(label)) return `${at} correct answer "${label}" matches no option label exactly`
    }
    if (!q.multiSelect && correct.length !== 1) {
      return `${at} has several correct answers: set multiSelect to true, or give one`
    }
  }
  return undefined
}

export function shuffled(items: readonly string[], random: () => number = Math.random): string[] {
  const out = [...items]
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

// The dialog answers with the chosen label(s), comma-joined for multi-select,
// or free text typed under "Other". Labels never contain commas (validate), so
// a multi-select answer splits cleanly; anything that is not a label is "other".
export function parseAnswer(raw: string, shown: readonly string[], multiSelect: boolean): { selected: string[]; other?: string } {
  const text = raw.trim()
  if (text === '') return { selected: [] }
  if (!multiSelect) {
    return shown.includes(text) ? { selected: [text] } : { selected: [], other: text }
  }
  const pieces = text.split(/,\s*/).filter(piece => piece !== '')
  const picked = new Set(pieces.filter(piece => shown.includes(piece)))
  const other = pieces.filter(piece => !shown.includes(piece)).join(', ')
  return { selected: shown.filter(option => picked.has(option)), ...(other ? { other } : {}) }
}

export function judge(raw: string, q: QuizQuestion, shown: string[]): Outcome {
  const correct = correctList(q)
  const multiSelect = q.multiSelect === true
  const base = { question: q.question, shown, multiSelect, correct, explanation: q.explanation }
  const { selected, other } = parseAnswer(raw, shown, multiSelect)

  if (selected.length > 0) {
    const isCorrect = selected.length === correct.length && correct.every(label => selected.includes(label))
    return { ...base, kind: 'graded', selected, isCorrect, ...(other ? { note: other } : {}) }
  }
  if (other && looksLikeDontKnow(other)) return { ...base, kind: 'dontKnow', selected: [] }
  return { ...base, kind: 'noAttempt', selected: [], ...(other ? { note: other } : {}) }
}

export function dismissed(q: QuizQuestion, shown: string[]): Outcome {
  return {
    kind: 'dismissed',
    question: q.question,
    shown,
    multiSelect: q.multiSelect === true,
    correct: correctList(q),
    explanation: q.explanation,
    selected: [],
  }
}

const labels = (items: string[]): string => items.join(', ')

// The line the learner sees right after answering.
export function feedbackLine(o: Outcome): string {
  if (o.kind === 'graded' && o.isCorrect) return `✓ Correct. ${o.explanation}`
  if (o.kind === 'graded') return `✗ Not quite. Correct answer: ${labels(o.correct)}. ${o.explanation}`
  return `Correct answer: ${labels(o.correct)}. ${o.explanation}`
}

// What the model reads back. `total` is how many questions the call held.
export function resultText(outcomes: Outcome[], total: number): string {
  const parts = outcomes.map((o, i) => {
    const lines: string[] = []
    if (total > 1) lines.push(`Question ${i + 1} of ${total}: ${o.question}`)
    if (o.kind === 'graded') {
      lines.push(`The learner answered ${o.isCorrect ? 'correctly' : 'incorrectly'}.`, `Selected: ${labels(o.selected)}`)
    } else if (o.kind === 'dontKnow') {
      lines.push(
        'The learner said "I don\'t know": they did not attempt an answer (a genuine knowledge gap, not a wrong guess).',
      )
    } else if (o.kind === 'noAttempt') {
      lines.push('The learner chose no option and wrote a note instead. Treat it as a gap to read and teach into, not a wrong answer.')
    } else {
      lines.push('The learner dismissed the quiz without answering.')
    }
    lines.push(`Correct: ${labels(o.correct)}`)
    if (o.note) lines.push(`Learner's note: ${o.note}`)
    lines.push(`Explanation: ${o.explanation}`)
    lines.push('Options as shown:', ...o.shown.map((option, j) => `${j + 1}. ${option}`))
    return lines.join('\n')
  })
  const unasked = total - outcomes.length
  if (unasked > 0) parts.push(`${unasked} further question${unasked === 1 ? ' was' : 's were'} not asked.`)
  return parts.join('\n\n')
}
