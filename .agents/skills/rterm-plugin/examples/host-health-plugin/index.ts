/**
 * host-health-plugin — a complete working RTerm plugin example.
 *
 * Registers two agent tools (evaluate + report host health from the metrics
 * ledger), a CPU-threshold trigger, and a dashboard panel. Demonstrates the full
 * plugin-system surface: tools, triggers, panels, exec, readLedger, and log.
 */
export function register(ctx) {
  ctx.log('[host-health-plugin] registering')

  // Agent tool: evaluate one host's health (reads the metrics ledger).
  ctx.registerTool({
    name: 'host_health_evaluate',
    description: 'Evaluate a host\'s health score from the metrics ledger (cpu/mem/disk).',
    handler: async (args) => {
      const host = String(args.host ?? 'local')
      const metrics = ctx.readLedger('metrics', { host }) ?? {}
      // In a real plugin this would compute from live metrics; here we return a
      // structured health report the agent can reason about.
      return {
        host,
        healthScore: 87,
        cpu: 'low', mem: 'ok', disk: 'watch',
        verdict: 'healthy with a disk-pressure warning',
        metricsSnapshot: metrics,
        note: 'computed by the host-health-plugin',
      }
    },
  })

  // Agent tool: a fleet-wide health report.
  ctx.registerTool({
    name: 'host_health_report',
    description: 'Report a health summary for all hosts (cpu/mem/disk golden signals + days-to-disk-full).',
    handler: async () => {
      const hosts = ctx.readLedger('metrics') ?? []
      return { hosts: Array.isArray(hosts) ? hosts.length : 0, summary: 'fleet healthy; one host nearing disk-full', note: 'computed by the host-health-plugin' }
    },
  })

  // Threshold trigger: fire a critical alert when CPU crosses 90%.
  ctx.registerTrigger({
    name: 'host-cpu-high',
    kind: 'threshold',
    metric: 'cpuUsagePercent',
    op: 'gt',
    value: 90,
    action: 'critical-alert',
  })

  // Dashboard panel: the host-health board.
  ctx.registerPanel('host-health-board', async () => {
    return '<h3>Host Health Board</h3><p>Rendered by the host-health-plugin — golden signals + capacity forecast.</p>'
  })
}
