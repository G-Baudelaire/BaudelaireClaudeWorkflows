// pdf-allow: let the pdf-reader agent run the plugin's own read-only PDF tool
// without a permission prompt. A background agent cannot answer a prompt, so
// without this it is simply denied and never opens the book.
//
// Deliberately narrow and fail-safe. It allows ONE thing: a plain command that
// runs <plugin>/scripts/pdf_tool.py with info, search, extract, render or where.
// Anything else (chaining, pipes, redirects, expansions, another script, another
// subcommand, anything it cannot parse) is left alone and asks as usual.

import type { Register } from 'claude-code'

// All read-only for the PDF; render writes only PNG files into the system temp folder.
const SUBCOMMANDS = new Set(['info', 'search', 'extract', 'render', 'where'])
const PYTHONS = new Set(['python', 'python3', 'py'])

// Characters that make a command more than a plain program call when unquoted.
const UNQUOTED_FORBIDDEN = /[;&|<>(){}`$*?[\]!#~\\\r\n]/

// Splits a command into words the way a shell would, but refuses (returns null)
// anything it cannot be sure of: unquoted shell syntax, expansions inside double
// quotes, or an unclosed quote.
export function tokenize(command: string): string[] | null {
  const tokens: string[] = []
  let current = ''
  let started = false
  let quote: '"' | "'" | null = null

  for (let i = 0; i < command.length; i++) {
    const c = command[i]
    if (quote === "'") {
      if (c === "'") quote = null
      else if (c === '\n' || c === '\r') return null
      else current += c
    } else if (quote === '"') {
      if (c === '"') quote = null
      else if (c === '$' || c === '`' || c === '\n' || c === '\r') return null
      else if (c === '\\' && '\\"$`'.includes(command[i + 1] ?? '')) return null
      else current += c
    } else if (c === '"' || c === "'") {
      quote = c
      started = true
    } else if (c === ' ' || c === '\t') {
      if (started || current) tokens.push(current)
      current = ''
      started = false
    } else if (UNQUOTED_FORBIDDEN.test(c)) {
      return null
    } else {
      current += c
      started = true
    }
  }
  if (quote) return null
  if (started || current) tokens.push(current)
  return tokens
}

const norm = (path: string): string => path.replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase()

export function isPdfToolCommand(command: string, pluginRoot: string): boolean {
  const tokens = tokenize(command.trim())
  if (!tokens || tokens.length < 3) return false
  const [python, script, sub] = tokens
  const root = norm(pluginRoot)
  if (!root) return false

  const isPlainPython = PYTHONS.has(python.toLowerCase())
  const venvPython = [`${root}/.venv/scripts/python.exe`, `${root}/.venv/bin/python`]
  const isVenvPython = venvPython.includes(norm(python))
  if (!isPlainPython && !isVenvPython) return false

  if (norm(script) !== `${root}/scripts/pdf_tool.py`) return false
  return SUBCOMMANDS.has(sub)
}

export const registerPdfAllow: Register = on => {
  on('tool.check', { tool: 'Bash' }, ($, e, next) => {
    const command = (e.input as { command?: unknown } | undefined)?.command
    if (typeof command === 'string' && isPdfToolCommand(command, $.plugin.root)) {
      return { decision: 'allow', reason: 'tutor: read-only PDF tool' }
    }
    return next(e)
  })

  on('tool.check', { tool: 'PowerShell' }, ($, e, next) => {
    const command = (e.input as { command?: unknown } | undefined)?.command
    if (typeof command === 'string' && isPdfToolCommand(command, $.plugin.root)) {
      return { decision: 'allow', reason: 'tutor: read-only PDF tool' }
    }
    return next(e)
  })
}
