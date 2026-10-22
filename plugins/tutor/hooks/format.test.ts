import { describe, expect, test } from 'claude-code/testing'

import {
  appendBlocks,
  quizCallouts,
  quizQuestionCallout,
  quizVerdictCallout,
  renderRow,
  stripNoise,
  type Block,
} from './format'
import { loggedCalls, type Outcome } from './quiz-logic'

describe('md-log formatting', () => {
  test('user prose becomes a YOU block, with injected noise removed', async () => {
    const content: Block[] = [
      { type: 'text', text: 'Teach me about <system-reminder>hidden</system-reminder>entropy' },
    ]
    const out = renderRow('user', content, new Map())
    expect(out).toEqual(['> [!quote] YOU\n\nTeach me about entropy'])
  })

  test('a row that is only noise logs nothing', async () => {
    expect(stripNoise('<system-reminder>x</system-reminder>')).toBe('')
    const out = renderRow('user', [{ type: 'text', text: '<command-name>/md-log</command-name>' }], new Map())
    expect(out).toEqual([])
  })

  test('assistant text becomes a CLAUDE block and thinking is left out', async () => {
    const content: Block[] = [
      { type: 'thinking', thinking: 'secret' },
      { type: 'text', text: 'Hello' },
    ]
    expect(renderRow('assistant', content, new Map())).toEqual(['> [!abstract] CLAUDE\n\nHello'])
  })

  test('an AskUserQuestion call becomes a question callout with numbered options and no answer key', async () => {
    const content: Block[] = [
      {
        type: 'tool_use',
        id: 't1',
        name: 'AskUserQuestion',
        input: {
          questions: [
            { question: 'Pick one?', header: 'Pick', options: [{ label: 'A' }, { label: 'B' }], multiSelect: false },
          ],
        },
      },
    ]
    const out = renderRow('assistant', content, new Map())
    expect(out).toEqual(['> [!question] Question — Pick\n> Pick one?\n>\n> 1. A\n> 2. B'])
  })

  test('fenced code and mermaid inside a question stay fenced, every line inside the callout', async () => {
    const question = 'What runs?\n\n```python\nclass Dog:\n    def speak(self): return 1\n\nDog().speak()\n```'
    const out = quizQuestionCallout({ question, shown: ['a', 'b'], multiSelect: false })
    expect(out).toBe(
      [
        '> [!question] Quiz',
        '> What runs?',
        '>',
        '> ```python',
        '> class Dog:',
        '>     def speak(self): return 1',
        '>',
        '> Dog().speak()',
        '> ```',
        '>',
        '> 1. a',
        '> 2. b',
      ].join('\n'),
    )
  })

  test('a tool_use_error result is not logged', async () => {
    const names = new Map<string, string>([['q1', 'mcp__tutor__quiz']])
    const result: Block = {
      type: 'tool_result',
      tool_use_id: 'q1',
      is_error: true,
      content: '<tool_use_error>quiz question 1 option labels cannot contain commas</tool_use_error>',
    }
    expect(renderRow('user', [result], names)).toEqual([])
  })

  test('its result is recognised by tool_use id, and by the engine hint when the call was never seen', async () => {
    const names = new Map<string, string>([['t1', 'AskUserQuestion']])
    const result: Block = { type: 'tool_result', tool_use_id: 't1', content: 'User answered: A' }
    expect(renderRow('user', [result], names)).toEqual(['> [!example] Answer\n> User answered: A'])
    expect(renderRow('user', [{ ...result, tool_use_id: 'zzz' }], new Map(), 'AskUserQuestion')).toEqual([
      '> [!example] Answer\n> User answered: A',
    ])
  })

  test('answers drop injected reminders and put each question and answer on its own line', async () => {
    const names = new Map<string, string>([['t1', 'AskUserQuestion']])
    const result: Block = {
      type: 'tool_result',
      tool_use_id: 't1',
      content:
        'Your questions have been answered: "Pick one?"="A", "And two?"="B, C". You can now continue.\n<system-reminder>\n<total_tokens>9</total_tokens>\n</system-reminder>',
    }
    expect(renderRow('user', [result], names)).toEqual([
      '> [!example] Answer\n> **Pick one?** → A\n> **And two?** → B, C',
    ])
  })

  test('a quiz is logged with the options as shown, a verdict callout, and the explanation only after the answer', async () => {
    const outcome: Outcome = {
      kind: 'graded',
      question: 'Which is even?',
      shown: ['9', '6', '11'],
      multiSelect: false,
      correct: ['6'],
      explanation: '6 divides by 2.',
      selected: ['9'],
      isCorrect: false,
    }
    const names = new Map<string, string>([['q1', 'mcp__tutor__quiz']])
    const result: Block = { type: 'tool_result', tool_use_id: 'q1', content: 'ignored: the outcome is used' }
    const out = renderRow('user', [result], names, undefined, new Map([['q1', [outcome]]]))
    expect(out).toEqual([
      '> [!question] Quiz\n> Which is even?\n>\n> 1. 9\n> 2. 6\n> 3. 11',
      '> [!failure] Quiz — incorrect ✗\n> Your answer: 1. 9\n> Correct answer: 2. 6\n>\n> 6 divides by 2.',
    ])
  })

  test('quiz verdict callouts: correct, don\'t know, no option chosen, dismissed', async () => {
    const base = { question: 'Q?', shown: ['a', 'b'], multiSelect: false, correct: ['a'], explanation: 'Because.', selected: [] }
    const titles = quizCallouts([
      { ...base, kind: 'graded', selected: ['a'], isCorrect: true },
      { ...base, kind: 'dontKnow' },
      { ...base, kind: 'noAttempt', note: 'maybe c' },
      { ...base, kind: 'dismissed' },
    ])
      .filter((_, i) => i % 2 === 1)
      .map(block => block.split('\n')[0])
    expect(titles).toEqual([
      '> [!success] Quiz — correct ✓',
      "> [!question] Quiz — I don't know",
      '> [!warning] Quiz — no option chosen',
      '> [!warning] Quiz — dismissed',
    ])
  })

  test('the question callout holds no answer key, and the verdict callout is separate', async () => {
    const outcome: Outcome = {
      kind: 'graded',
      question: 'Which is even?',
      shown: ['9', '6'],
      multiSelect: false,
      correct: ['6'],
      explanation: '6 divides by 2.',
      selected: ['6'],
      isCorrect: true,
    }
    const asked = quizQuestionCallout(outcome)
    expect(asked).toBe('> [!question] Quiz\n> Which is even?\n>\n> 1. 9\n> 2. 6')
    expect(asked).not.toContain('divides')
    expect(quizVerdictCallout(outcome)).toContain('[!success] Quiz — correct ✓')
  })

  test('a quiz the quiz tool already logged live is not logged again', async () => {
    loggedCalls.add('live1')
    const names = new Map<string, string>([['live1', 'mcp__tutor__quiz']])
    const result: Block = { type: 'tool_result', tool_use_id: 'live1', content: 'The learner answered correctly.' }
    expect(renderRow('user', [result], names, undefined, new Map())).toEqual([])
    loggedCalls.delete('live1')
  })

  test('a quiz from before logging started falls back to the result text', async () => {
    const names = new Map<string, string>([['q9', 'mcp__tutor__quiz']])
    const result: Block = { type: 'tool_result', tool_use_id: 'q9', content: 'The learner answered correctly.' }
    expect(renderRow('user', [result], names, undefined, new Map())).toEqual([
      '> [!note] Quiz (earlier)\n> The learner answered correctly.',
    ])
  })

  test('results of other tools are not logged', async () => {
    const result: Block = { type: 'tool_result', tool_use_id: 't9', content: 'file contents' }
    expect(renderRow('user', [result], new Map([['t9', 'Read']]))).toEqual([])
  })

  test('appending keeps the existing note and separates blocks with blank lines', async () => {
    expect(appendBlocks('# Note', ['a', 'b'])).toBe('# Note\n\na\n\nb\n')
    expect(appendBlocks('', ['a'])).toBe('a\n')
    expect(appendBlocks('keep', [])).toBe('keep')
  })
})
