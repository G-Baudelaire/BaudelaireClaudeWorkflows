import { describe, expect, test } from 'claude-code/testing'

import {
  correctList,
  dismissed,
  feedbackLine,
  judge,
  looksLikeDontKnow,
  parseAnswer,
  resultText,
  shuffled,
  validate,
  type QuizQuestion,
} from './quiz-logic'

const single: QuizQuestion = {
  question: 'Which is even?',
  options: ['6', '9', '11'],
  correct: '6',
  explanation: '6 divides by 2.',
}

const multi: QuizQuestion = {
  question: 'Which are even?',
  options: ['2', '3', '4', '5'],
  correct: ['2', '4'],
  explanation: '2 and 4 divide by 2.',
  multiSelect: true,
}

describe('validate', () => {
  test('accepts well-formed single and multi-select questions', async () => {
    expect(validate({ questions: [single, multi] })).toBeUndefined()
  })

  test('rejects the wrong number of questions', async () => {
    expect(validate({ questions: [] })).toBe('quiz needs 1 to 4 questions')
    expect(validate({ questions: [single, single, single, single, single] })).toBe('quiz needs 1 to 4 questions')
  })

  test('rejects a correct answer that matches no option exactly', async () => {
    expect(validate({ questions: [{ ...single, correct: '6 ' }] })).toContain('matches no option label exactly')
  })

  test('rejects bad option sets', async () => {
    expect(validate({ questions: [{ ...single, options: ['6'] }] })).toContain('2 to 4 options')
    expect(validate({ questions: [{ ...single, options: ['6', '6', '9'] }] })).toContain('distinct')
    expect(validate({ questions: [{ ...single, options: ['6', '9, 11'], correct: '6' }] })).toContain('commas')
    expect(validate({ questions: [{ ...single, options: ['1', '2', '3', '4', '5'] }] })).toContain('2 to 4 options')
  })

  test('rejects several correct answers unless multiSelect is set', async () => {
    expect(validate({ questions: [{ ...single, correct: ['6', '9'] }] })).toContain('multiSelect')
  })

  test('requires an explanation and question text', async () => {
    expect(validate({ questions: [{ ...single, explanation: ' ' }] })).toContain('explanation')
    expect(validate({ questions: [{ ...single, question: '' }] })).toContain('question text')
  })
})

describe('correctList', () => {
  test('reads a list sent as a JSON string, and a plain label', async () => {
    expect(correctList({ correct: '["2","4"]' })).toEqual(['2', '4'])
    expect(correctList({ correct: '6' })).toEqual(['6'])
    expect(correctList({ correct: ['2', '4'] })).toEqual(['2', '4'])
  })
})

describe('shuffled', () => {
  test('keeps the same options and does not change the input', async () => {
    const options = ['a', 'b', 'c', 'd']
    const out = shuffled(options, () => 0)
    expect([...out].sort()).toEqual(['a', 'b', 'c', 'd'])
    expect(options).toEqual(['a', 'b', 'c', 'd'])
  })
})

describe('parseAnswer', () => {
  test('single-select: a label is selected, other text is an "other"', async () => {
    expect(parseAnswer('6', ['6', '9'], false)).toEqual({ selected: ['6'] })
    expect(parseAnswer('well, maybe 7', ['6', '9'], false)).toEqual({ selected: [], other: 'well, maybe 7' })
    expect(parseAnswer('  ', ['6', '9'], false)).toEqual({ selected: [] })
  })

  test('multi-select: comma-joined labels split in display order, extra text is an "other"', async () => {
    expect(parseAnswer('4, 2', ['2', '3', '4'], true)).toEqual({ selected: ['2', '4'] })
    expect(parseAnswer('2, not sure', ['2', '3', '4'], true)).toEqual({ selected: ['2'], other: 'not sure' })
  })
})

describe('looksLikeDontKnow', () => {
  test('recognises the usual phrasings and nothing else', async () => {
    for (const text of ['idk', 'IDK', "I don't know", 'i dont know', "don't know", 'dunno', 'not sure', 'idk.']) {
      expect(looksLikeDontKnow(text)).toBe(true)
    }
    expect(looksLikeDontKnow('idk but maybe 6')).toBe(false)
    expect(looksLikeDontKnow('six')).toBe(false)
  })
})

describe('judge', () => {
  const shown = ['9', '6', '11']

  test('single-select right and wrong', async () => {
    expect(judge('6', single, shown)).toMatchObject({ kind: 'graded', isCorrect: true, selected: ['6'] })
    expect(judge('9', single, shown)).toMatchObject({ kind: 'graded', isCorrect: false, selected: ['9'] })
  })

  test('multi-select is an exact-set match', async () => {
    const order = ['3', '2', '5', '4']
    expect(judge('2, 4', multi, order)).toMatchObject({ kind: 'graded', isCorrect: true })
    expect(judge('2', multi, order)).toMatchObject({ kind: 'graded', isCorrect: false })
    expect(judge('2, 4, 5', multi, order)).toMatchObject({ kind: 'graded', isCorrect: false })
  })

  test('idk is a don\'t-know, never a wrong answer', async () => {
    const outcome = judge('idk', single, shown)
    expect(outcome.kind).toBe('dontKnow')
    expect(outcome.isCorrect).toBeUndefined()
  })

  test('other free text with no option is a no-attempt note', async () => {
    expect(judge('I would say 8', single, shown)).toMatchObject({ kind: 'noAttempt', note: 'I would say 8' })
  })

  test('a note typed alongside a chosen option is kept with the graded answer', async () => {
    expect(judge('2, because they halve', multi, ['2', '3', '4', '5'])).toMatchObject({
      kind: 'graded',
      note: 'because they halve',
    })
  })
})

describe('text for the model and the learner', () => {
  const shown = ['9', '6', '11']

  test('a single question has no "Question n of m" header and lists the options as shown', async () => {
    const text = resultText([judge('6', single, shown)], 1)
    expect(text).toContain('The learner answered correctly.')
    expect(text).toContain('Selected: 6')
    expect(text).toContain('Options as shown:\n1. 9\n2. 6\n3. 11')
    expect(text).not.toContain('Question 1 of')
  })

  test('a dismissed batch says how many questions were not asked', async () => {
    const text = resultText([judge('6', single, shown), dismissed(multi, ['2', '3', '4', '5'])], 4)
    expect(text).toContain('Question 1 of 4')
    expect(text).toContain('Question 2 of 4')
    expect(text).toContain('dismissed the quiz')
    expect(text).toContain('2 further questions were not asked.')
  })

  test('the don\'t-know text says it is a gap, not a wrong guess', async () => {
    expect(resultText([judge('idk', single, shown)], 1)).toContain('a genuine knowledge gap, not a wrong guess')
  })

  test('the feedback line shows a tick, or a cross with the right answer', async () => {
    expect(feedbackLine(judge('6', single, shown))).toBe('✓ Correct. 6 divides by 2.')
    expect(feedbackLine(judge('9', single, shown))).toBe('✗ Not quite. Correct answer: 6. 6 divides by 2.')
    expect(feedbackLine(judge('idk', single, shown))).toBe('Correct answer: 6. 6 divides by 2.')
  })
})
