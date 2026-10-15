import { describe, expect, test } from 'claude-code/testing'

import { isPdfToolCommand, tokenize } from './pdf-allow'

const ROOT = 'C:\\Users\\someone\\plugins\\tutor'
const SCRIPT = `"${ROOT}\\scripts\\pdf_tool.py"`
const ok = (command: string): boolean => isPdfToolCommand(command, ROOT)

describe('commands that are allowed without a prompt', () => {
  test('each subcommand of the plugin script, however python is spelled', async () => {
    expect(ok(`python ${SCRIPT} info "C:\\books\\calculus.pdf"`)).toBe(true)
    expect(ok(`python3 ${SCRIPT} where`)).toBe(true)
    expect(ok(`py ${SCRIPT} extract "C:\\books\\calculus.pdf" --pages 8-9 --max-chars 5000`)).toBe(true)
    expect(ok(`python ${SCRIPT} render "C:\\books\\calculus.pdf" --pages 8 --dpi 130`)).toBe(true)
    expect(ok(`python ${SCRIPT} search "C:\\books\\calculus.pdf" "epsilon" --literal --max-matches 10`)).toBe(true)
  })

  test('forward slashes, different case, and the plugin\'s own venv python', async () => {
    expect(ok(`python "c:/users/someone/plugins/tutor/scripts/pdf_tool.py" info "x.pdf"`)).toBe(true)
    expect(ok(`"${ROOT}\\.venv\\Scripts\\python.exe" ${SCRIPT} info "x.pdf"`)).toBe(true)
  })

  test('a search query may contain regex punctuation when it is quoted', async () => {
    expect(ok(`python ${SCRIPT} search "x.pdf" "epsilon|delta (small)"`)).toBe(true)
    expect(ok(`python ${SCRIPT} search 'x.pdf' 'a;b && c'`)).toBe(true)
  })
})

describe('commands that still ask', () => {
  test('chaining, pipes, redirects and substitutions', async () => {
    for (const tail of [
      '; rm -rf /',
      '&& echo hi',
      '| sort',
      '> out.txt',
      '$(whoami)',
      '`whoami`',
      '& calc',
    ]) {
      expect(ok(`python ${SCRIPT} info "x.pdf" ${tail}`)).toBe(false)
    }
  })

  test('expansions inside double quotes', async () => {
    expect(ok(`python ${SCRIPT} search "x.pdf" "$HOME"`)).toBe(false)
    expect(ok(`python ${SCRIPT} search "x.pdf" "\`id\`"`)).toBe(false)
  })

  test('a newline smuggling in a second command', async () => {
    expect(ok(`python ${SCRIPT} info "x.pdf"\nrm -rf /`)).toBe(false)
  })

  test('any other script, a traversal, or another plugin\'s folder', async () => {
    expect(ok(`python "${ROOT}\\scripts\\other.py" info "x.pdf"`)).toBe(false)
    expect(ok(`python "${ROOT}\\scripts\\..\\..\\evil\\pdf_tool.py" info "x.pdf"`)).toBe(false)
    expect(ok(`python "C:\\elsewhere\\scripts\\pdf_tool.py" info "x.pdf"`)).toBe(false)
  })

  test('other subcommands, other interpreters, and options before the script', async () => {
    expect(ok(`python ${SCRIPT} install "x.pdf"`)).toBe(false)
    expect(ok(`python ${SCRIPT}`)).toBe(false)
    expect(ok(`bash ${SCRIPT} info "x.pdf"`)).toBe(false)
    expect(ok(`python -c "print(1)" ${SCRIPT} info "x.pdf"`)).toBe(false)
    expect(ok(`FOO=1 python ${SCRIPT} info "x.pdf"`)).toBe(false)
  })

  test('things it cannot parse: an unclosed quote, an unquoted backslash path', async () => {
    expect(ok(`python ${SCRIPT} info "x.pdf`)).toBe(false)
    expect(ok(`python ${SCRIPT} info C:\\books\\x.pdf`)).toBe(false)
    expect(ok('')).toBe(false)
  })

  test('an empty plugin root allows nothing', async () => {
    expect(isPdfToolCommand(`python ${SCRIPT} info "x.pdf"`, '')).toBe(false)
  })
})

describe('tokenize', () => {
  test('splits words and keeps quoted text together', async () => {
    expect(tokenize(`a "b c" 'd e' f`)).toEqual(['a', 'b c', 'd e', 'f'])
    expect(tokenize(`a ""`)).toEqual(['a', ''])
    expect(tokenize('a; b')).toBeNull()
  })
})
