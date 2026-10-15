// The plugin's one hooks module: a plugin names a single module, so each
// feature registers its own hooks from here. Session start is done once, here,
// because the engine allows only one unmatched session.start hook per module.

import type { Register } from 'claude-code'

import { MD_LOG_COMMANDS, registerMdLog } from './md-log'
import { registerPdfAllow } from './pdf-allow'
import { QUIZ_TOOL, registerQuiz } from './quiz'

export const register: Register = (on, options) => {
  on('session.start', async ($, e, next) => {
    for (const command of MD_LOG_COMMANDS) await $.command.register(command)
    await $.tool.register(QUIZ_TOOL)

    // A reloaded plugin keeps its per-session link: show it again.
    const { value } = await $.state.get({ plugin: 'tutor', key: 'mdLog' } as const)
    const file = value?.file
    $.ui.status(file ? `🗒 ${file.split(/[\\/]/).pop()}` : undefined)
    return next(e)
  })

  registerMdLog(on, options)
  registerQuiz(on, options)
  registerPdfAllow(on, options)
}
