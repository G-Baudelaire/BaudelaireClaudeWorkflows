// Appending to the linked markdown note. Shared by md-log and the quiz tool,
// so every write goes through one queue and none overwrites another.
//
// The engine handle `$` cannot be passed across a file boundary, so callers hand
// in the four things this needs as plain functions (see fileIo in each caller).

import { appendBlocks } from './format'

export type FileIo = {
  exists: (path: string) => Promise<boolean>
  read: (path: string) => Promise<unknown>
  write: (path: string, text: string) => Promise<void>
  status: (text: string) => void
}

// The file API has no append, so each write reads and rewrites the whole note.
// Rows can arrive close together, so keep the writes strictly in order.
let chain: Promise<void> = Promise.resolve()

export function nameOf(path: string): string {
  return path.split(/[\\/]/).pop() ?? path
}

export async function appendToFile(io: FileIo, file: string, blocks: string[]): Promise<void> {
  if (blocks.length === 0) return
  const job = async (): Promise<void> => {
    // The note must already exist; if it was deleted, stay quiet rather than recreate it.
    if (!(await io.exists(file))) return
    try {
      const current = String(await io.read(file))
      await io.write(file, appendBlocks(current, blocks))
    } catch {
      io.status(`md-log: could not write ${nameOf(file)}`)
    }
  }
  chain = chain.then(job).catch(() => {})
  await chain
}
