---
name: superagent-cli
description: Use the SuperAgent CLI to orchestrate worktrees, live terminals, and browser automation through a running SuperAgent editor. Use when an agent needs to create, inspect, update, or remove SuperAgent worktrees; inspect repo state known to SuperAgent; read, send to, wait on, or stop SuperAgent-managed terminals; or automate the built-in browser (navigate, snapshot, click, fill, screenshot). Coding agents should also keep the current worktree comment updated with the latest meaningful work-in-progress checkpoint whenever useful. Triggers include "use superagent cli", "manage SuperAgent worktrees", "read SuperAgent terminal", "reply to Claude Code in SuperAgent", "create a worktree in SuperAgent", "update SuperAgent worktree comment", "click on", "fill the form", "take a screenshot", "navigate to", "interact with the page", "snapshot the page", or any task where the agent should operate through SuperAgent.
---

# SuperAgent CLI

Use this skill when the task should go through SuperAgent's control plane rather than directly through `git`, shell PTYs, or ad hoc filesystem access.

## When To Use

Use `superagent` for:

- worktree orchestration inside a running SuperAgent app
- updating the current worktree comment with meaningful progress checkpoints
- reading and replying to SuperAgent-managed terminals
- stopping or waiting on SuperAgent-managed terminals
- accessing repos known to SuperAgent
  Do not use `superagent` when plain shell tools are simpler and SuperAgent state does not matter.

Examples:

- creating one SuperAgent worktree per GitHub issue
- updating the current worktree comment after a significant checkpoint, such as reproducing a bug, validating a fix, or handing off for review
- finding the Claude Code terminal for a worktree and replying to it
- checking which SuperAgent worktrees have live terminal activity

## Preconditions

- Prefer the public `superagent` command first
- SuperAgent editor/runtime should already be running, or the agent should start it with `superagent open`
- Do not begin by inspecting SuperAgent source files just to decide how to invoke the CLI. The first step is to check whether the installed `superagent` command exists.
- Do not assume a generic shell environment variable proves the agent is "inside SuperAgent". For normal agent flows, the public CLI is the supported surface, but avoid wasting a round trip on probe-only checks when a direct SuperAgent action would answer the question.

First verify the public CLI is installed:

```bash
command -v superagent
```

Then use the public command:

```bash
superagent status --json
```

If the task is about SuperAgent worktrees or SuperAgent terminals, do this before any codebase exploration:

```bash
command -v superagent
superagent status --json
```

If the agent truly needs to confirm that the current directory is inside an SuperAgent-managed worktree, use:

```bash
superagent worktree current --json
```

If `superagent` is not on PATH, say so explicitly and stop or ask the user to install/register the CLI before continuing.

## Core Workflow

1. Confirm SuperAgent runtime availability:

```bash
superagent status --json
```

If SuperAgent is not running yet:

```bash
superagent open --json
superagent status --json
```

2. Discover current SuperAgent state:

```bash
superagent worktree ps --json
superagent terminal list --json
```

3. Resolve a target worktree or terminal handle.

4. Act through SuperAgent:

- `worktree create/set/rm`
- `terminal read/send/wait/stop`

5. When the agent reaches a significant checkpoint in the current worktree, update the SuperAgent worktree comment so the UI reflects the latest work-in-progress:

```bash
superagent worktree set --worktree active --comment "reproduced auth failure with aws sts; testing credential-chain fix" --json
```

Why: the worktree comment is SuperAgent's lightweight, agent-writable status field. Keeping it current gives the user an at-a-glance summary of what the agent most recently proved, changed, or is waiting on.

## Command Surface

### Repo

```bash
superagent repo list --json
superagent repo show --repo id:<repoId> --json
superagent repo add --path /abs/repo --json
superagent repo set-base-ref --repo id:<repoId> --ref origin/main --json
superagent repo search-refs --repo id:<repoId> --query main --limit 10 --json
```

### Worktree

```bash
superagent worktree list --repo id:<repoId> --json
superagent worktree ps --json
superagent worktree current --json
superagent worktree show --worktree id:<worktreeId> --json
superagent worktree create --repo id:<repoId> --name my-task --issue 123 --comment "seed" --json
superagent worktree set --worktree id:<worktreeId> --display-name "My Task" --json
superagent worktree set --worktree active --comment "reproduced bug; collecting logs from staging" --json
superagent worktree set --worktree active --comment "waiting on review" --json
superagent worktree rm --worktree id:<worktreeId> --force --json
```

Worktree selectors supported in focused v1:

- `id:<worktree-id>`
- `path:<absolute-path>`
- `branch:<branch-name>`
- `issue:<number>`
- `active` / `current` to resolve the enclosing SuperAgent-managed worktree from the shell `cwd`

### Terminal

Use selectors to discover terminals, then use the returned handle for repeated live interaction.

```bash
superagent terminal list --worktree id:<worktreeId> --json
superagent terminal show --terminal <handle> --json
superagent terminal read --terminal <handle> --json
superagent terminal send --terminal <handle> --text "continue" --enter --json
superagent terminal wait --terminal <handle> --for exit --timeout-ms 5000 --json
superagent terminal wait --terminal <handle> --for tui-idle --timeout-ms 30000 --json
superagent terminal stop --worktree id:<worktreeId> --json
superagent terminal create --json
superagent terminal create --title "My Terminal" --json
superagent terminal create --worktree path:/projects/myapp --command "npm test" --json
superagent terminal split --terminal <handle> --direction vertical --json
superagent terminal split --terminal <handle> --direction horizontal --command "npm run dev" --json
superagent terminal rename --terminal <handle> --title "New Name" --json
superagent terminal switch --terminal <handle> --json
superagent terminal close --terminal <handle> --json
superagent terminal send --text "echo hello" --enter --json
superagent terminal read --json
```

Why: `--terminal` is optional for most commands. When omitted, SuperAgent auto-resolves to the active terminal in the current worktree (same as browser commands target the active tab). Use explicit `--terminal <handle>` when operating on a specific pane.

Why: terminal handles are runtime-scoped and may go stale after reloads. If SuperAgent returns `terminal_handle_stale`, reacquire a fresh handle with `terminal list`.

Why: `--direction horizontal` splits the pane **left and right** (new pane appears to the right). `--direction vertical` splits the pane **top and bottom** (new pane appears below). This matches VS Code's split convention. Default is horizontal.

## Agent Guidance

- If the user says to create/manage an SuperAgent worktree, use `superagent worktree ...`, not raw `git worktree ...`.
- Treat SuperAgent as the source of truth for SuperAgent worktree and terminal tasks. Do not mix SuperAgent-managed state with ad hoc git worktree commands unless SuperAgent explicitly cannot perform the requested action.
- Prefer `--json` for all machine-driven use.
- Use `worktree ps` as the first summary view when many worktrees may exist.
- Use `worktree current` or `--worktree active` when the agent is already running inside the target worktree.
- Treat `superagent worktree set --worktree active --comment ... --json` as a default coding-agent behavior whenever the agent reaches a meaningful checkpoint in the current SuperAgent-managed worktree; the user does not need to explicitly ask for each update.
- Update the worktree comment at significant checkpoints, not every trivial command. Good checkpoints include reproducing a bug, confirming a hypothesis, starting a risky migration, finishing a meaningful implementation slice, switching from investigation to fix, or blocking on external input.
- Write comments as short status snapshots of the current state, for example `debugging AWS CLI profile resolution`, `confirmed flaky test is caused by temp-dir race`, or `fix implemented; running integration tests`.
- Prefer optimistic execution over probe-first flows for checkpoint updates: if `superagent` is on `PATH`, call `superagent worktree set --worktree active --comment ... --json` directly at the checkpoint instead of spending an extra cycle on `superagent worktree current`.
- If that direct update fails because SuperAgent is unavailable or the shell is not inside an SuperAgent-managed worktree, continue the main task and treat the comment update as best-effort unless the user explicitly made SuperAgent state part of the task.
- Use `superagent worktree current --json` only when the agent actually needs the worktree identity for later logic, not as a preflight before every comment update.
- SuperAgent only injects `ORCA_WORKTREE_PATH`-style variables for some setup-hook flows, so they are not a general detection contract for agents.
- Use `terminal list` to reacquire handles after SuperAgent reloads.
- Use `terminal read` before `terminal send` unless the next input is obvious.
- Use `terminal wait --terminal <handle> --for exit` only when the task actually depends on process completion.
- Use `terminal wait --terminal <handle> --for tui-idle` to wait for an agent CLI (Claude Code, Gemini, Codex, etc.) to finish its current task. This detects the working→idle OSC title transition. Always pass `--timeout-ms` as a safety net — unsupported CLIs will hang until timeout.
- Use `terminal create` to spin up new terminal tabs programmatically, optionally with a `--command` for startup (e.g. `--command "claude"` to launch Claude Code) and `--title` for labeling. After creating a `--command` terminal, use `terminal wait --for tui-idle` to wait for the agent to boot before dispatching.
- Use `terminal split` to create split panes within an existing terminal tab. Pass `--command` to run a command in the new pane.
- Prefer SuperAgent worktree selectors over hardcoded paths when SuperAgent identity already exists.
- If the user asks for CLI UX feedback, test the public `superagent` command first. Only inspect `src/cli` or use `node out/cli/index.js` if the public command is missing or the task is explicitly about implementation internals.
- If a command fails, prefer retrying with the public `superagent` command before concluding the CLI is broken, unless the failure already came from `superagent` itself.

## Browser Automation

The `superagent` CLI also drives the built-in SuperAgent browser. The core workflow is a **snapshot-interact-re-snapshot** loop:

1. **Snapshot** the page to see interactive elements and their refs.
2. **Interact** using refs (`@e1`, `@e3`, etc.) to click, fill, or select.
3. **Re-snapshot** after interactions to see the updated page state.

```bash
superagent goto --url https://example.com --json
superagent snapshot --json
# Read the refs from the snapshot output
superagent click --element @e3 --json
superagent snapshot --json
```

### Element Refs

Refs like `@e1`, `@e5` are short identifiers assigned to interactive page elements during a snapshot. They are:

- **Assigned by snapshot**: Run `superagent snapshot` to get current refs.
- **Scoped to one tab**: Refs from one tab are not valid in another.
- **Invalidated by navigation**: If the page navigates after a snapshot, refs become stale. Re-snapshot to get fresh refs.
- **Invalidated by tab switch**: Switching tabs with `superagent tab switch` invalidates refs. Re-snapshot after switching.

If a ref is stale, the command returns `browser_stale_ref` — re-snapshot and retry.

### Worktree Scoping

Browser commands default to the **current worktree** — only tabs belonging to the agent's worktree are visible and targetable. Tab indices are relative to the filtered tab list.

```bash
# Default: operates on tabs in the current worktree
superagent snapshot --json

# Explicitly target all worktrees (cross-worktree access)
superagent snapshot --worktree all --json

# Tab indices are relative to the worktree-filtered list
superagent tab list --json         # Shows tabs [0], [1], [2] for this worktree
superagent tab switch --index 1 --json   # Switches to tab [1] within this worktree
```

If no tabs are open in the current worktree, commands return `browser_no_tab`.

### Stable Page Targeting

For single-agent flows, bare browser commands are fine: SuperAgent will target the active browser tab in the current worktree.

For concurrent or multi-process browser automation, prefer a stable page id instead of ambient active-tab state:

1. Run `superagent tab list --json`.
2. Read `tabs[].browserPageId` from the result.
3. Pass `--page <browserPageId>` to follow-up commands like `snapshot`, `click`, `goto`, `screenshot`, `tab switch`, or `tab close`.

Why: active-tab state and tab indices can change while another SuperAgent CLI process is working. `browserPageId` pins the command to one concrete tab.

```bash
superagent tab list --json
superagent snapshot --page page-123 --json
superagent click --page page-123 --element @e3 --json
superagent screenshot --page page-123 --json
superagent tab switch --page page-123 --json
superagent tab close --page page-123 --json
```

If you also pass `--worktree`, SuperAgent treats it as extra scoping/validation for that page id. Without `--page`, commands still fall back to the current worktree's active tab.

### Navigation

```bash
superagent goto --url <url> [--json]           # Navigate to URL, waits for page load
superagent back [--json]                       # Go back in browser history
superagent forward [--json]                    # Go forward in browser history
superagent reload [--json]                     # Reload the current page
```

### Observation

```bash
superagent snapshot [--page <browserPageId>] [--json]                   # Accessibility tree snapshot with element refs
superagent screenshot [--page <browserPageId>] [--format <png|jpeg>] [--json]  # Viewport screenshot (base64)
superagent full-screenshot [--page <browserPageId>] [--format <png|jpeg>] [--json]  # Full-page screenshot (base64)
superagent pdf [--page <browserPageId>] [--json]                        # Export page as PDF (base64)
```

### Interaction

```bash
superagent click --element <ref> [--page <browserPageId>] [--json]      # Click an element by ref
superagent dblclick --element <ref> [--page <browserPageId>] [--json]   # Double-click an element
superagent fill --element <ref> --value <text> [--page <browserPageId>] [--json]  # Clear and fill an input
superagent type --input <text> [--page <browserPageId>] [--json]        # Type at current focus (no element targeting)
superagent select --element <ref> --value <value> [--page <browserPageId>] [--json]  # Select dropdown option
superagent check --element <ref> [--page <browserPageId>] [--json]      # Check a checkbox
superagent uncheck --element <ref> [--page <browserPageId>] [--json]    # Uncheck a checkbox
superagent scroll --direction <up|down> [--amount <pixels>] [--page <browserPageId>] [--json]  # Scroll viewport
superagent scrollintoview --element <ref> [--page <browserPageId>] [--json]  # Scroll element into view
superagent hover --element <ref> [--page <browserPageId>] [--json]      # Hover over an element
superagent focus --element <ref> [--page <browserPageId>] [--json]      # Focus an element
superagent drag --from <ref> --to <ref> [--page <browserPageId>] [--json]  # Drag from one element to another
superagent clear --element <ref> [--page <browserPageId>] [--json]      # Clear an input field
superagent select-all --element <ref> [--page <browserPageId>] [--json] # Select all text in an element
superagent keypress --key <key> [--page <browserPageId>] [--json]       # Press a key (Enter, Tab, Escape, etc.)
superagent upload --element <ref> --files <paths> [--page <browserPageId>] [--json]  # Upload files to a file input
```

### Tab Management

```bash
superagent tab list [--json]                   # List open browser tabs
superagent tab switch (--index <n> | --page <browserPageId>) [--json]     # Switch active tab (invalidates refs)
superagent tab create [--url <url>] [--json]   # Open a new browser tab
superagent tab close [--index <n> | --page <browserPageId>] [--json]    # Close a browser tab
```

### Wait / Synchronization

```bash
superagent wait [--timeout <ms>] [--json]                        # Wait for timeout (default 1000ms)
superagent wait --selector <css> [--state <visible|hidden>] [--timeout <ms>] [--json]  # Wait for element
superagent wait --text <string> [--timeout <ms>] [--json]        # Wait for text to appear on page
superagent wait --url <substring> [--timeout <ms>] [--json]      # Wait for URL to contain substring
superagent wait --load <networkidle|load|domcontentloaded> [--timeout <ms>] [--json]   # Wait for load state
superagent wait --fn <js-expression> [--timeout <ms>] [--json]   # Wait for JS condition to be truthy
```

After any page-changing action, pick one:

- Wait for specific content: `superagent wait --text "Dashboard" --json`
- Wait for URL change: `superagent wait --url "/dashboard" --json`
- Wait for network idle (catch-all for SPA navigation): `superagent wait --load networkidle --json`
- Wait for an element: `superagent wait --selector ".results" --json`

Avoid bare `superagent wait --timeout 2000` except when debugging — it makes scripts slow and flaky.

### Data Extraction

```bash
superagent exec --command "get text @e1" [--json]   # Get visible text of an element
superagent exec --command "get html @e1" [--json]   # Get innerHTML
superagent exec --command "get value @e1" [--json]  # Get input value
superagent exec --command "get attr @e1 href" [--json]  # Get element attribute
superagent exec --command "get title" [--json]      # Get page title
superagent exec --command "get url" [--json]        # Get current URL
superagent exec --command "get count .item" [--json]      # Count matching elements
```

### State Checks

```bash
superagent exec --command "is visible @e1" [--json]  # Check if element is visible
superagent exec --command "is enabled @e1" [--json]  # Check if element is enabled
superagent exec --command "is checked @e1" [--json]  # Check if checkbox is checked
```

### Page Inspection

```bash
superagent eval --expression <js> [--json]     # Evaluate JS in page context
```

### Cookie Management

```bash
superagent cookie get [--url <url>] [--json]   # List cookies
superagent cookie set --name <n> --value <v> [--domain <d>] [--json]  # Set a cookie
superagent cookie delete --name <n> [--domain <d>] [--json]  # Delete a cookie
```

### Emulation

```bash
superagent viewport --width <w> --height <h> [--scale <n>] [--mobile] [--json]
superagent geolocation --latitude <lat> --longitude <lng> [--accuracy <m>] [--json]
```

### Request Interception

```bash
superagent intercept enable [--patterns <list>] [--json]  # Start intercepting requests
superagent intercept disable [--json]          # Stop intercepting
superagent intercept list [--json]             # List paused requests
```

> **Note:** Per-request `intercept continue` and `intercept block` are not yet supported.
> They will be added once agent-browser supports per-request interception decisions.

### Console / Network Capture

```bash
superagent capture start [--json]              # Start capturing console + network
superagent capture stop [--json]               # Stop capturing
superagent console [--limit <n>] [--json]      # Read captured console entries
superagent network [--limit <n>] [--json]      # Read captured network entries
```

### Mouse Control

```bash
superagent exec --command "mouse move 100 200" [--json]   # Move mouse to coordinates
superagent exec --command "mouse down left" [--json]      # Press mouse button
superagent exec --command "mouse up left" [--json]        # Release mouse button
superagent exec --command "mouse wheel 100" [--json]      # Scroll wheel
```

### Keyboard

```bash
superagent exec --command "keyboard inserttext \"text\"" [--json]  # Insert text bypassing key events
superagent exec --command "keyboard type \"text\"" [--json]        # Raw keystrokes
superagent exec --command "keydown Shift" [--json]                 # Hold key down
superagent exec --command "keyup Shift" [--json]                   # Release key
```

### Frames (Iframes)

Iframes are auto-inlined in snapshots — refs inside iframes work transparently. For scoped interaction:

```bash
superagent exec --command "frame @e3" [--json]        # Switch to iframe by ref
superagent exec --command "frame \"#iframe\"" [--json] # Switch to iframe by CSS selector
superagent exec --command "frame main" [--json]       # Return to main frame
```

### Semantic Locators (alternative to refs)

When refs aren't available or you want to skip a snapshot:

```bash
superagent exec --command "find role button click --name \"Submit\"" [--json]
superagent exec --command "find text \"Sign In\" click" [--json]
superagent exec --command "find label \"Email\" fill \"user@test.com\"" [--json]
superagent exec --command "find placeholder \"Search\" type \"query\"" [--json]
superagent exec --command "find testid \"submit-btn\" click" [--json]
```

### Dialogs

`alert` and `beforeunload` are auto-accepted. For `confirm` and `prompt`:

```bash
superagent exec --command "dialog status" [--json]        # Check for pending dialog
superagent exec --command "dialog accept" [--json]        # Accept
superagent exec --command "dialog accept \"text\"" [--json]  # Accept with prompt input
superagent exec --command "dialog dismiss" [--json]       # Dismiss/cancel
```

### Extended Commands (Passthrough)

```bash
superagent exec --command "<agent-browser command>" [--json]
```

The `exec` command provides access to agent-browser's full command surface. Useful for commands without typed SuperAgent handlers:

```bash
superagent exec --command "set device \"iPhone 14\"" --json   # Emulate device
superagent exec --command "set offline on" --json             # Toggle offline mode
superagent exec --command "set media dark" --json             # Emulate color scheme
superagent exec --command "network requests" --json           # View tracked network requests
superagent exec --command "help" --json                       # See all available commands
```

**Important:** Do not use `superagent exec --command "tab ..."` for tab management. Use `superagent tab list/create/close/switch` instead — those operate at the SuperAgent level and keep the UI synchronized.

### `fill` vs `type`

- **`fill`** targets a specific element by ref, clears its value first, then enters text. Use for form fields.
- **`type`** types at whatever currently has focus. Use for search boxes or after clicking into an input.

If neither works on a custom input component, try:

```bash
superagent focus --element @e1 --json
superagent exec --command "keyboard inserttext \"text\"" --json   # bypasses key events
```

### Browser Error Codes

| Error Code              | Meaning                                      | Recovery                                                                                     |
| ----------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `browser_no_tab`        | No browser tab is open in this worktree      | Open a tab, or use `--worktree all` to check other worktrees                                 |
| `browser_stale_ref`     | Ref is invalid (page changed since snapshot) | Run `superagent snapshot` to get fresh refs                                                        |
| `browser_tab_not_found` | Tab index does not exist                     | Run `superagent tab list` to see available tabs                                                    |
| `browser_error`         | Error from the browser automation engine     | Read the message for details; common causes: element not found, navigation timeout, JS error |

### Browser Worked Example

Agent fills a login form and verifies the dashboard loads:

```bash
# Navigate to the login page
superagent goto --url https://app.example.com/login --json

# See what's on the page
superagent snapshot --json
# Output includes:
#   [@e1] text input "Email"
#   [@e2] text input "Password"
#   [@e3] button "Sign In"

# Fill the form
superagent fill --element @e1 --value "user@example.com" --json
superagent fill --element @e2 --value "s3cret" --json

# Submit
superagent click --element @e3 --json

# Verify the dashboard loaded
superagent snapshot --json
# Output should show dashboard content, not the login form
```

### Browser Troubleshooting

**"Ref not found" / `browser_stale_ref`**
Page changed since the snapshot. Run `superagent snapshot --json` again, then use the new refs.

**Element exists but not in snapshot**
It may be off-screen or not yet rendered. Try:

```bash
superagent scroll --direction down --amount 1000 --json
superagent snapshot --json
# or wait for it:
superagent wait --text "..." --json
superagent snapshot --json
```

**Click does nothing / overlay swallows the click**
Modals or cookie banners may be blocking. Snapshot, find the dismiss button, click it, then re-snapshot.

**Fill/type doesn't work on a custom input**
Some components intercept key events. Use `keyboard inserttext`:

```bash
superagent focus --element @e1 --json
superagent exec --command "keyboard inserttext \"text\"" --json
```

**`browser_no_tab` error**
No browser tab is open in the current worktree. Open one with `superagent tab create --url <url> --json`.

### Auto-Switch Worktree

Browser commands automatically activate the target worktree in the SuperAgent UI when needed. If the agent issues a browser command targeting a worktree that isn't currently active, SuperAgent will switch to that worktree before executing the command.

### Tab Create Auto-Activation

When `superagent tab create` opens a new tab, it is automatically set as the active tab for the worktree. Subsequent commands (`snapshot`, `click`, etc.) will target the newly created tab without needing an explicit `tab switch`.

### Browser Agent Guidance

- Always snapshot before interacting with elements.
- After navigation (`goto`, `back`, `reload`, clicking a link), re-snapshot to get fresh refs.
- After switching tabs, re-snapshot.
- If you get `browser_stale_ref`, re-snapshot and retry with the new refs.
- Use `superagent tab list` before `superagent tab switch` to know which tabs exist.
- For concurrent browser workflows, prefer `superagent tab list --json` and reuse `tabs[].browserPageId` with `--page` on later commands.
- Use `superagent wait` to synchronize after actions that trigger async updates (form submits, SPA navigation, modals) instead of arbitrary sleeps.
- Use `superagent eval` as an escape hatch for interactions not covered by other commands.
- Use `superagent exec --command "help"` to discover extended commands.
- Worktree scoping is automatic — you'll only see tabs from your worktree by default.
- Bare browser commands without `--page` still target the current worktree's active tab, which is convenient but less robust for multi-process automation.
- Tab creation auto-activates the new tab — no need for `tab switch` after `tab create`.
- Browser commands auto-switch the active worktree if needed — no manual worktree activation required.

## Important Constraints

- SuperAgent CLI only talks to a running SuperAgent editor.
- Terminal handles are ephemeral and tied to the current SuperAgent runtime. If SuperAgent restarts, handles change.
- `terminal wait` supports `--for exit` (wait for process exit) and `--for tui-idle` (wait for a recognized agent CLI like Claude Code, Gemini, or Codex to finish its current task, detected via OSC title transitions). `tui-idle` defaults to a 5-minute timeout if `--timeout-ms` is not specified. Real coding tasks routinely take 15-60 minutes — always pass `--timeout-ms` explicitly.
- SuperAgent is the source of truth for worktree/terminal state; do not duplicate that state with manual assumptions.
- The public `superagent` command is the interface users experience. Agents should validate and use that surface, not repo-local implementation entrypoints.
- The 120-line terminal output buffer (`terminal read`) is for status monitoring, not result extraction.

## References

See these docs in this repo when behavior is unclear:

- `docs/orca-cli-focused-v1-status.md`
- `docs/orca-cli-v1-spec.md`
- `docs/superagent-runtime-layer-design.md`
