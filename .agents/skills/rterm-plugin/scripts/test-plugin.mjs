#!/usr/bin/env node
// NOTE: run this with tsx (the pluginRegistry is TypeScript with parameter properties).
//   node_modules/.bin/tsx scripts/test-plugin.mjs --dir ./plugins/hello
// or, from this skill's dir:
//   tsx scripts/test-plugin.mjs --dir ./plugins/hello
/**
 * test-plugin.mjs — load an RTerm plugin via the REAL PluginRegistry (the exact
 * code RTerm uses) and report what it registered + prove a tool executes.
 *
 * Usage:
 *   tsx scripts/test-plugin.mjs --dir ./plugins/hello
 *   tsx scripts/test-plugin.mjs --dir ./plugins/hello --tool hello_greet --args '{"name":"olu"}'
 */
import process from 'node:process'
import path from 'node:path'
import { PluginRegistry } from '/Users/olu/work/RTerm/packages/backend/src/services/plugin/pluginRegistry.ts'

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

const DIR = argv.dir
if (!DIR) { console.error('usage: node test-plugin.mjs --dir ./plugins/hello [--tool NAME --args <json>]'); process.exit(2) }

async function main() {
  const logs = []
  const registry = new PluginRegistry({
    scanRoots: [],
    createContext: (rec) => PluginRegistry.defaultContext(
      rec,
      async (cmd, opts) => `[exec] ${cmd} on ${opts?.host ?? 'local'}`,
      (name) => ({ ledger: name, note: 'stub ledger (test mode)' }),
      (l) => logs.push(l),
    ),
    now: () => Date.now(),
    onLog: (l) => logs.push(l),
  })

  const abs = path.resolve(DIR)
  const rec = await registry.loadFromDir(abs)
  if (!rec) { console.error(`✗ plugin at ${abs} did not load (no record)`); process.exit(1) }

  console.log(`✓ loaded ${rec.manifest.name}@${rec.manifest.version}${rec.error ? `  [error: ${rec.error}]` : ''}`)
  console.log(`  enabled: ${rec.enabled}`)
  console.log(`  tools:    ${rec.tools.map((t) => t.name).join(', ') || '(none)'}`)
  console.log(`  triggers: ${rec.triggers.map((t) => `${t.name} [${t.kind}]`).join(', ') || '(none)'}`)
  console.log(`  panels:   ${rec.panels.map((p) => p.name).join(', ') || '(none)'}`)
  console.log(`  allTools: ${registry.allTools().length} | allTriggers: ${registry.allTriggers().length} | allPanels: ${registry.allPanels().length}`)

  // Optionally call a tool to prove it executes.
  if (argv.tool) {
    const tool = rec.tools.find((t) => t.name === argv.tool)
    if (!tool) { console.error(`✗ tool "${argv.tool}" not found in plugin`); process.exit(3) }
    let args = {}
    try { args = argv.args ? JSON.parse(argv.args) : {} } catch { console.error('✗ --args is not valid JSON'); process.exit(4) }
    const out = await tool.handler(args)
    console.log(`\n  ${argv.tool}(${JSON.stringify(args)}) ->`)
    console.log(' ', JSON.stringify(out, null, 2))
  }

  if (rec.panels.length > 0) {
    const html = await rec.panels[0].render()
    console.log(`\n  panel "${rec.panels[0].name}" renders: ${String(html).slice(0, 120)}`)
  }

  if (logs.length > 0) {
    console.log('\n  plugin log lines:')
    for (const l of logs) console.log('   ', l)
  }
  console.log('\n✓ plugin loads + registers correctly (this is the exact PluginRegistry RTerm uses)')
}

void main().catch((e) => { console.error('✗', e.message); process.exit(1) })
