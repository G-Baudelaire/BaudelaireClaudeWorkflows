// md-log: mirror this session into a markdown note (e.g. an Obsidian vault file).
//
//   /md-log <filepath>  link an existing note and backfill the session into it
//   /md-unlog           stop logging
//
// Logged: what the person typed, what Claude wrote, and AskUserQuestion and quiz
// questions and answers. Tool calls, thinking and subagent traffic are left out.
// The link is per session (kept in $.state), so a new session starts unlinked.
// A quiz question is written live by the quiz tool itself, before it is asked.

import type { EngineInterface, Register } from 'claude-code'

import { renderRow, type Block, type Role } from './format'
import { appendToFile, nameOf, type FileIo } from './log-file'
import { outcomesByCall } from './quiz-logic'

// tool_use id -> tool name, so a later tool_result can be recognised.
const names = new Map<string, string>()

function fileIo($: EngineInterface): FileIo {
  return {
    exists: path => $.fs.exists(path),
    read: path => $.fs.read(path),
    write: (path, text) => $.fs.write(path, text),
    status: text => $.ui.status(text),
  }
}

function showLinked($: EngineInterface, file: string | null): void {
  $.ui.status(file ? `🗒 ${nameOf(file)}` : undefined)
}

// Registered once at session start, by index.ts (one unmatched session.start hook per module).
export const MD_LOG_COMMANDS = [
  {
    name: 'md-log',
    description: 'Mirror this session into a markdown note (backfills what is said so far)',
    argumentHint: '<filepath>',
  },
  { name: 'md-unlog', description: 'Stop mirroring this session into a markdown note' },
]

export const registerMdLog: Register = on => {
  on('command.run', { command: 'md-log' }, async ($, e) => {
    const given = e.args.trim().replace(/^["']|["']$/g, '')
    if (!given) return { text: 'Usage: /md-log <filepath>' }

    if (!(await $.fs.exists(given))) {
      return { text: `File does not exist: ${given}. /md-log links an existing note; it never creates one.` }
    }
    const stat = await $.fs.stat(given)
    if (stat.kind !== 'file') return { text: `Not a file: ${given}` }

    await $.state.set({ plugin: 'tutor', key: 'mdLog' } as const, { file: given })

    // Backfill the conversation so far, appended after whatever the note holds.
    const blocks: string[] = []
    for (const message of await $.session.messages({ as: 'api' })) {
      blocks.push(...renderRow(message.role as Role, message.content as Block[], names, undefined, outcomesByCall))
    }
    await appendToFile(fileIo($), given, blocks)

    showLinked($, given)
    return { text: `Linked: ${given} (${blocks.length} entries backfilled)` }
  })

  on('command.run', { command: 'md-unlog' }, async $ => {
    const { value } = await $.state.get({ plugin: 'tutor', key: 'mdLog' } as const)
    if (!value?.file) return { text: 'No file linked.' }
    await $.state.set({ plugin: 'tutor', key: 'mdLog' } as const, { file: null })
    showLinked($, null)
    return { text: `Unlinked: ${nameOf(value.file)}` }
  })

  on('session.append', async ($, e, next) => {
    const stored = await next(e)

    // Only the main conversation's prose rows and question traffic.
    if (e.agentId) return stored
    if (e.door !== 'prompt' && e.door !== 'response' && e.door !== 'tool-result') return stored
    const type = e.message.type
    if (type !== 'user' && type !== 'assistant') return stored
    if (e.message.isMeta) return stored

    // The row is already stored; a logging failure must never fail the hook.
    try {
      const { value } = await $.state.get({ plugin: 'tutor', key: 'mdLog' } as const)
      const file = value?.file
      if (!file) return stored

      const hintTool = e.origin.kind === 'tool' ? e.origin.tool : undefined
      const blocks = renderRow(type as Role, e.message.content as Block[], names, hintTool, outcomesByCall)
      await appendToFile(fileIo($), file, blocks)
    } catch {
      $.ui.status('md-log: could not log a row')
    }
    return stored
  })
}
