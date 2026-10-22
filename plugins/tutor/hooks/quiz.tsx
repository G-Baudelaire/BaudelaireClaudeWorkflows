// quiz: a graded question the plugin owns. The model sends the question
// together with the answer key; the hook shuffles, asks, grades, and the
// transcript row shows only the question, never the key.

import type { EngineInterface, Register } from 'claude-code'

import { quizQuestionCallout, quizVerdictCallout } from './format'
import { appendToFile, type FileIo } from './log-file'
import {
  dismissed,
  feedbackLine,
  judge,
  loggedCalls,
  outcomesByCall,
  resultText,
  shuffled,
  validate,
  type Outcome,
  type QuizInput,
} from './quiz-logic'

function fileIo($: EngineInterface): FileIo {
  return {
    exists: path => $.fs.exists(path),
    read: path => $.fs.read(path),
    write: (path, text) => $.fs.write(path, text),
    status: text => $.ui.status(text),
  }
}

// Registered once at session start, by index.ts (one unmatched session.start hook per module).
export const QUIZ_TOOL = {
  name: 'quiz',
  description:
    'Ask the learner 1 to 4 GRADED multiple-choice questions, each with a known correct answer. ' +
    'You supply the options and the correct one(s); the plugin shuffles the options, asks, grades, ' +
    'and shows the learner a check or cross with your explanation. You get the verdict back. ' +
    'Use it to map what the learner already knows before teaching, and to check a step landed after teaching. ' +
    'Use AskUserQuestion instead for preferences or decisions that have no right answer.\n\n' +
    'How to write a good question:\n' +
    '- Probing: ask ONE question per call and adapt the next to the last answer. Use several questions in one call only for independent checks.\n' +
    '- Every option is a bare claim with no justification. Put all the reasoning in `explanation`, which is shown only after answering.\n' +
    '- Write the correct claim first, then mutate it into each wrong option in the same wording, length and style, so the right one cannot be picked from its shape.\n' +
    '- Each wrong option is a specific, believable mistake (a real misconception or an easily confused neighbour), so WHICH one the learner picks shows which gap to teach into. It must still be unambiguously wrong, never a trick.\n' +
    '- `correct` is copied exactly from `options`. For several correct options set `multiSelect` to true and pass a list; it is graded as an exact set.\n' +
    '- Options are shuffled for you. Set `shuffle` to false only when order matters (ordered values, "All of the above").\n' +
    '- Do NOT add an "I don\'t know" option. The learner types "idk" under Other, and you get back a don\'t-know result: a genuine gap, not a wrong answer. Anything else they type under Other comes back as a note.\n' +
    '- Code in a question goes in a fenced block with a language tag (```python), never bare indented lines: the session note renders markdown, and bare code loses its indentation there.\n' +
    '- Option labels cannot contain commas.',
  inputSchema: {
    type: 'object',
    properties: {
      questions: {
        type: 'array',
        minItems: 1,
        maxItems: 4,
        description: 'The questions, asked one after another.',
        items: {
          type: 'object',
          properties: {
            question: { type: 'string', description: 'The single question to ask.' },
            options: {
              type: 'array',
              items: { type: 'string' },
              minItems: 2,
              maxItems: 4,
              description: 'The answer options as bare claims: 2 to 4, distinct, no commas.',
            },
            correct: {
              anyOf: [{ type: 'string' }, { type: 'array', items: { type: 'string' } }],
              description: 'The correct option label, copied exactly from options. A list when multiSelect is true.',
            },
            explanation: {
              type: 'string',
              description: 'Why the correct answer is correct. Shown to the learner after they answer.',
            },
            multiSelect: { type: 'boolean', description: 'True when more than one option is correct.' },
            shuffle: { type: 'boolean', description: 'Defaults to true. False keeps the option order.' },
            header: { type: 'string', description: 'Short chip beside the question, 12 characters at most.' },
          },
          required: ['question', 'options', 'correct', 'explanation'],
        },
      },
    },
    required: ['questions'],
  },
  isDeferred: false as const,
}

export const registerQuiz: Register = on => {
  // The call must not raise a permission prompt: the prompt would show the key.
  on('tool.check', { tool: 'mcp__tutor__quiz' }, () => ({ decision: 'allow', reason: 'tutor quiz' })).catch(() => ({
    decision: 'allow',
    reason: 'tutor quiz',
  }))

  on('tool.call', { tool: 'mcp__tutor__quiz' }, async ($, e) => {
    const input = e as unknown as QuizInput
    const problem = validate(input)
    if (problem) return { deny: problem }

    // When a note is linked, each question goes into it BEFORE it is asked, so
    // the learner can read it rendered (the dialog shows raw LaTeX). The verdict
    // follows once they answer. md-log then skips this call (loggedCalls).
    const callId = String((e as { tool_use_id?: string }).tool_use_id ?? '')
    const link = await $.state.get({ plugin: 'tutor', key: 'mdLog' } as const)
    const file = link.value?.file ?? null

    const outcomes: Outcome[] = []
    for (const q of input.questions) {
      const shown = q.shuffle === false ? [...q.options] : shuffled(q.options)
      if (file) {
        await appendToFile(fileIo($), file, [
          quizQuestionCallout({ question: q.question, shown, multiSelect: q.multiSelect === true }),
        ])
      }

      let raw: string
      try {
        raw = await $.ui.ask(q.question, {
          options: shown,
          header: (q.header ?? 'Quiz').slice(0, 12),
          ...(q.multiSelect ? { multiSelect: true as const } : {}),
        })
      } catch {
        const skipped = dismissed(q, shown)
        outcomes.push(skipped)
        if (file) await appendToFile(fileIo($), file, [quizVerdictCallout(skipped)])
        break
      }
      const outcome = judge(raw, q, shown)
      outcomes.push(outcome)
      $.ui.log(feedbackLine(outcome))
      if (file) await appendToFile(fileIo($), file, [quizVerdictCallout(outcome)])
    }

    outcomesByCall.set(callId, outcomes)
    if (file) loggedCalls.add(callId)
    return { result: resultText(outcomes, input.questions.length) }
  })

  // The transcript row shows the question(s) only, never the answer key.
  on('ui.render', { component: 'ToolUse', tool: 'mcp__tutor__quiz' }, ($, e) => {
    const { Text } = $.ui.resolve(e)
    const questions = ((e.props.input ?? {}) as Partial<QuizInput>).questions
    const list = Array.isArray(questions) ? questions : []
    const first = list.length > 0 ? String(list[0]?.question ?? '') : ''
    const more = list.length > 1 ? ` (+${list.length - 1} more)` : ''
    return <Text>quiz: {first}{more}</Text>
  })
}
