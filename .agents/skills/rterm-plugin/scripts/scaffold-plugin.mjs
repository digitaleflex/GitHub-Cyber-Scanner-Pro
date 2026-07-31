#!/usr/bin/env node
/**
 * scaffold-plugin.mjs — scaffold a new RTerm plugin folder (manifest + entry).
 *
 * Usage:
 *   node scaffold-plugin.mjs --name my-plugin [--out ./plugins] [--with-trigger] [--with-panel]
 */
import process from 'node:process'
import fs from 'node:fs'
import path from 'node:path'

const argv = (() => {
  const a = {}
  for (let i = 2; i < process.argv.length; i += 1) {
    if (process.argv[i].startsWith('--')) {
      const k = process.argv[i].slice(2); const n = process.argv[i + 1]
      if (n === undefined || n.startsWith('--')) a[k] = true; else { a[k] = n; i += 1 }
    }
  }
  return a
})()

const NAME = (argv.name || '').toString().trim().replace(/[^A-Za-z0-9_-]/g, '-')
const OUT = argv.out || './plugins'
if (!NAME) { console.error('usage: node scaffold-plugin.mjs --name my-plugin [--out ./plugins] [--with-trigger] [--with-panel]'); process.exit(2) }

const dir = path.join(OUT, NAME)
if (fs.existsSync(dir)) { console.error(`plugin folder already exists: ${dir}`); process.exit(1) }
fs.mkdirSync(dir, { recursive: true })

const tools = [`${NAME.replace(/-/g, '_')}_action`]
const manifest = {
  name: NAME,
  version: '1.0.0',
  description: `${NAME} — a custom RTerm plugin`,
  author: process.env.USER || 'you',
  entry: 'index.ts',
  tools,
  ...(argv['with-trigger'] ? { triggers: [{ name: `${NAME}-trigger`, kind: 'pattern', match: 'ERROR' }] } : {}),
  ...(argv['with-panel'] ? { panels: [`${NAME}-panel`] } : {}),
  permissions: ['exec_command', 'read_ledger'],
}
fs.writeFileSync(path.join(dir, 'plugin.json'), JSON.stringify(manifest, null, 2) + '\n')

const toolName = tools[0]
const triggerBlock = argv['with-trigger'] ? `
  // Event-driven trigger: fire when a pattern matches terminal output.
  ctx.registerTrigger({
    name: '${NAME}-trigger',
    kind: 'pattern',
    match: 'ERROR',
    action: 'critical-alert',
  })
` : ''
const panelBlock = argv['with-panel'] ? `
  // Dashboard panel: render custom HTML in the unified dashboard.
  ctx.registerPanel('${NAME}-panel', async () => '<h3>${NAME} Panel</h3><p>Rendered by the ${NAME} plugin.</p>')
` : ''

const indexTs = `/**
 * ${NAME} — a custom RTerm plugin.
 *
 * RTerm discovers this folder, loads index.ts, and calls register(ctx) with
 * RTerm's services. Your capabilities (agent tools, triggers, panels) appear
 * automatically — no RTerm code changes needed.
 */
export function register(ctx) {
  ctx.log('[${NAME}] registering')

  // Agent tool: the agent can call ${toolName}.
  ctx.registerTool({
    name: '${toolName}',
    description: 'Describe what this tool does.',
    handler: async (args) => {
      // Example: run something and return structured data the agent can use.
      return { tool: '${toolName}', args, note: 'implement your logic here (e.g. via ctx.exec or ctx.readLedger)' }
    },
  })
${triggerBlock}${panelBlock}}

/** Optional teardown on disable/uninstall. */
export function unregister() {
  // clean up resources if any
}
`
fs.writeFileSync(path.join(dir, 'index.ts'), indexTs)

console.log(`✓ scaffolded plugin at ${dir}`)
console.log(`  - plugin.json (edit description/permissions)`)
console.log(`  - index.ts (implement register(ctx))`)
console.log(`\nNext: edit index.ts, then test it:`)
console.log(`  node scripts/test-plugin.mjs --dir ${dir}`)
