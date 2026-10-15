export type MdLogState = { file: string | null }

declare module 'claude-code' {
  interface PluginState {
    tutor: { mdLog: MdLogState }
  }
}
