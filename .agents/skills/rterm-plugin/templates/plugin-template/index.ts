/**
 * plugin-template — a minimal RTerm plugin template.
 *
 * RTerm discovers this folder, loads index.ts, and calls register(ctx) with
 * RTerm's services. Your capabilities appear automatically.
 */
export function register(ctx) {
  ctx.log('[plugin-template] registering')

  // Agent tool: the agent can call plugin_template_action.
  ctx.registerTool({
    name: 'plugin_template_action',
    description: 'Describe what this tool does.',
    handler: async (args) => {
      return { tool: 'plugin_template_action', args, note: 'implement your logic here' }
    },
  })
}

/** Optional teardown on disable/uninstall. */
export function unregister() {}
