---
description: Automates browser interactions for web testing, form filling, screenshots, and data extraction. Use when the user needs to navigate websites, interact with web pages, fill forms, take screenshots, test web applications, or extract information from web pages.
name: agent-browser
source: https://github.com/vercel-labs/agent-browser
---

# Browser Automation with agent-browser

Fast native Rust CLI for AI agent browser automation. Uses Chrome via CDP (Chrome DevTools Protocol) with a client-daemon architecture — the daemon persists between commands for fast subsequent operations.

## Installation

```bash
npm install -g agent-browser
agent-browser install  # Download Chrome from Chrome for Testing (first time only)

# Or via Homebrew
brew install agent-browser
agent-browser install

# Or via Cargo
cargo install agent-browser
agent-browser install

# Upgrade
agent-browser upgrade
```

## Quick Start

```bash
agent-browser open <url>              # Navigate to page
agent-browser snapshot -i             # Get interactive elements with refs (@e1, @e2)
agent-browser click @e2               # Click element by ref
agent-browser fill @e3 "text"         # Fill input by ref
agent-browser screenshot page.png     # Screenshot
agent-browser close                   # Close browser
```

Clicks fail early when another element covers the target's click point. Dismiss or interact with the covering element, then take a fresh snapshot before retrying.

## Core Workflow

1. Navigate: `agent-browser open <url>`
2. Snapshot: `agent-browser snapshot -i` (returns elements with refs like `@e1`, `@e2`)
3. Interact using refs from the snapshot
4. Re-snapshot after navigation or significant DOM changes

## Commands

### Navigation
```bash
agent-browser open <url>              # Navigate to URL (aliases: goto, navigate)
agent-browser open                    # Launch browser (no navigation); stays on about:blank
agent-browser read [url]              # Fetch agent-readable text, or read rendered active-tab DOM
agent-browser back                    # Go back
agent-browser forward                 # Go forward
agent-browser reload                  # Reload page
agent-browser close                   # Close browser (aliases: quit, exit)
agent-browser close --all             # Close all active sessions
```

### Snapshot (page analysis)
```bash
agent-browser snapshot                # Full accessibility tree with refs
agent-browser snapshot -i             # Interactive elements only (recommended)
agent-browser snapshot -i --urls      # Interactive elements with link URLs
agent-browser snapshot -c             # Compact output (remove empty structural elements)
agent-browser snapshot -d 3           # Limit depth to 3 levels
agent-browser snapshot -s "#main"     # Scope to CSS selector
agent-browser snapshot -i -c -d 5     # Combine options
```

### Read Agent-Friendly Text
```bash
agent-browser read                            # Read rendered DOM of active tab
agent-browser read https://example.com        # Fetch URL as markdown
agent-browser read https://example.com --outline    # Compact heading outline
agent-browser read https://docs.example.com --llms index  # Nearest llms.txt links
agent-browser read https://docs.example.com --llms full   # Read llms-full.txt
agent-browser read url --filter overview      # Narrow page sections
agent-browser read url --require-md           # Fail unless Content-Type: text/markdown
```

### Interactions (use @refs from snapshot)
```bash
agent-browser click @e1               # Click
agent-browser click @e1 --new-tab     # Click and open in new tab
agent-browser dblclick @e1            # Double-click
agent-browser focus @e1               # Focus element
agent-browser fill @e2 "text"         # Clear and type
agent-browser type @e2 "text"         # Type without clearing
agent-browser press Enter             # Press key
agent-browser press Control+a         # Key combination
agent-browser keydown Shift           # Hold key down
agent-browser keyup Shift             # Release key
agent-browser keyboard type "text"    # Type with real keystrokes (no selector, current focus)
agent-browser keyboard inserttext "text"  # Insert text without key events
agent-browser hover @e1               # Hover
agent-browser check @e1               # Check checkbox
agent-browser uncheck @e1             # Uncheck checkbox
agent-browser select @e1 "value"      # Select dropdown
agent-browser scroll down 500         # Scroll page (up/down/left/right)
agent-browser scroll down --selector @e1  # Scroll specific element
agent-browser scrollintoview @e1      # Scroll element into view (alias: scrollinto)
agent-browser drag @e1 @e2            # Drag and drop
agent-browser upload @e1 file.pdf     # Upload files
```

### Get Information
```bash
agent-browser get text @e1            # Get element text
agent-browser get html @e1            # Get innerHTML
agent-browser get value @e1           # Get input value
agent-browser get attr @e1 href       # Get attribute
agent-browser get title               # Get page title
agent-browser get url                 # Get current URL
agent-browser get cdp-url             # Get CDP WebSocket URL (for DevTools)
agent-browser get count ".item"       # Count matching elements
agent-browser get box @e1             # Get bounding box
agent-browser get styles @e1          # Get computed styles
```

### Check State
```bash
agent-browser is visible @e1          # Check if visible
agent-browser is enabled @e1          # Check if enabled
agent-browser is checked @e1          # Check if checked
```

### Screenshots & PDF
```bash
agent-browser screenshot              # Screenshot to stdout (temp dir if no path)
agent-browser screenshot path.png     # Save to file
agent-browser screenshot --full       # Full page
agent-browser screenshot --annotate   # Annotated with numbered element labels
agent-browser screenshot --screenshot-dir ./shots
agent-browser screenshot --screenshot-format jpeg --screenshot-quality 80
agent-browser pdf output.pdf          # Save as PDF
```

### Annotated Screenshots
```bash
agent-browser screenshot --annotate ./page.png
# [1] @e1 button "Submit"
# [2] @e2 link "Home"
# [3] @e3 textbox "Email"

# After annotated screenshot, refs are cached for immediate interaction:
agent-browser click @e2
```

### Batch Execution
```bash
agent-browser batch "open https://example.com" "snapshot -i" "screenshot"
agent-browser batch --bail "open https://example.com" "click @e1" "screenshot"

# Stdin mode: pipe commands as JSON
echo '[["open","https://example.com"],["snapshot","-i"],["screenshot"]]' | agent-browser batch --json
```

### Clipboard
```bash
agent-browser clipboard read                      # Read text from clipboard
agent-browser clipboard write "Hello, World!"     # Write text to clipboard
agent-browser clipboard copy                      # Copy current selection (Ctrl+C)
agent-browser clipboard paste                     # Paste from clipboard (Ctrl+V)
```

### Video Recording
```bash
agent-browser record start ./demo.webm    # Start recording
agent-browser click @e1                   # Perform actions
agent-browser record stop                 # Stop and save video
agent-browser record restart ./take2.webm # Stop current + start new recording
```

### Wait
```bash
agent-browser wait @e1                     # Wait for element to be visible
agent-browser wait 2000                    # Wait milliseconds
agent-browser wait --text "Success"        # Wait for text to appear (substring match)
agent-browser wait --url "**/dashboard"    # Wait for URL pattern
agent-browser wait --load networkidle      # Wait for load state (load, domcontentloaded, networkidle)
agent-browser wait --fn "window.ready"     # Wait for JS condition
agent-browser wait "#spinner" --state hidden  # Wait for element to disappear
```

### Mouse Control
```bash
agent-browser mouse move 100 200      # Move mouse
agent-browser mouse down left         # Press button (left/right/middle)
agent-browser mouse up left           # Release button
agent-browser mouse wheel 100         # Scroll wheel
```

### Semantic Locators (alternative to refs)
```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find placeholder "Search" fill "query"
agent-browser find alt "Logo" click
agent-browser find first ".item" click
agent-browser find nth 2 "a" text
agent-browser find last ".item" click
# Actions: click, fill, type, hover, focus, check, uncheck, text
# Options: --name <name>, --exact
```

### Diff
```bash
agent-browser diff snapshot                              # Compare current vs last snapshot
agent-browser diff snapshot --baseline before.txt        # Compare current vs saved snapshot file
```

### Browser Settings
```bash
agent-browser set viewport 1920 1080 [scale]  # Set viewport size (scale for retina)
agent-browser set device "iPhone 14"          # Emulate device
agent-browser set geo 37.7749 -122.4194       # Set geolocation
agent-browser set offline on                  # Toggle offline mode
agent-browser set headers '{"X-Key":"v"}'     # Extra HTTP headers
agent-browser set credentials user pass       # HTTP basic auth
agent-browser set media dark                  # Emulate color scheme (dark/light)
```

### Cookies & Storage
```bash
agent-browser cookies                         # Get all cookies
agent-browser cookies set name value          # Set cookie
agent-browser cookies set --curl <file>       # Import from Copy-as-cURL dump
agent-browser cookies clear                   # Clear cookies
agent-browser storage local                   # Get all localStorage
agent-browser storage local key               # Get specific key
agent-browser storage local set k v           # Set value
agent-browser storage local clear             # Clear all
agent-browser storage session                 # Same for sessionStorage
```

### Network
```bash
agent-browser network route <url>              # Intercept requests
agent-browser network route <url> --abort      # Block requests
agent-browser network route <url> --body '{}'  # Mock response
agent-browser network route '*' --abort --resource-type script  # Block scripts only
agent-browser network unroute [url]            # Remove routes
agent-browser network requests                 # View tracked requests
agent-browser network requests --filter api    # Filter requests
agent-browser network requests --type xhr,fetch  # Filter by resource type
agent-browser network requests --method POST   # Filter by HTTP method
agent-browser network requests --status 2xx    # Filter by status
agent-browser network request <requestId>      # View full request/response detail
agent-browser network har start                # Start HAR recording
agent-browser network har stop [output.har]    # Stop and save HAR
```

### Tabs & Windows
```bash
agent-browser tab                              # List tabs (shows tabId and optional label)
agent-browser tab new [url]                    # New tab
agent-browser tab new --label docs [url]       # New tab with label
agent-browser tab t1                           # Switch to tab by id
agent-browser tab docs                         # Switch to tab by label
agent-browser tab close [t1|label]             # Close tab (defaults to active)
agent-browser window new                       # New window
```

Tab ids are stable strings: `t1`, `t2`, `t3`. Never reused within a session. You can also assign labels:
```bash
agent-browser tab new --label docs https://docs.example.com
agent-browser tab docs               # switch to docs tab
agent-browser tab close docs         # close by label
```

### Frames
```bash
agent-browser frame "#iframe"         # Switch to iframe
agent-browser frame main              # Back to main frame
```

### Dialogs
```bash
agent-browser dialog accept [text]    # Accept (with optional prompt text)
agent-browser dialog dismiss          # Dismiss
agent-browser dialog status           # Check if a dialog is currently open
```

By default, `alert` and `beforeunload` dialogs are auto-accepted. `confirm` and `prompt` require explicit handling. Use `--no-auto-dialog` to disable automatic handling.

### JavaScript
```bash
agent-browser eval "document.title"           # Run JavaScript
agent-browser eval -b "base64EncodedScript"   # Base64 encoded script
agent-browser eval --stdin                    # Piped input
```

### Init Scripts
```bash
agent-browser open --init-script <path>           # Register page init script before navigation
agent-browser addinitscript <js>                  # Register at runtime
agent-browser removeinitscript <identifier>       # Remove
```

### Streaming (Browser Preview)
```bash
agent-browser stream enable [--port <port>]   # Start runtime WebSocket streaming
agent-browser stream status                   # Show streaming state and bound port
agent-browser stream disable                  # Stop streaming
```

### Dashboard (Observability)
```bash
agent-browser dashboard start                 # Start dashboard on port 4848
agent-browser dashboard start --port 8080     # Custom port
agent-browser dashboard stop                  # Stop dashboard
```

Shows live viewport, activity feed, console output, session creation, and optional AI chat.

### AI Chat
```bash
agent-browser chat "open google.com and search for cats"  # Single-shot
agent-browser chat                                        # Interactive REPL
agent-browser -q chat "summarize this page"               # Quiet mode
agent-browser -v chat "fill in the login form"            # Verbose
agent-browser --model openai/gpt-4o chat "take a screenshot"
```

Requires `AI_GATEWAY_API_KEY` environment variable.

### Diff
```bash
agent-browser diff snapshot                              # Compare current vs last snapshot
agent-browser diff snapshot --baseline before.txt        # Compare current vs saved file
```

## Sessions (parallel browsers)

```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
agent-browser session                 # Show current session
```

Each session has its own browser instance, cookies, storage, navigation history, and auth state.

## Authentication

### Chrome Profile Reuse
```bash
agent-browser profiles                            # List available Chrome profiles
agent-browser --profile Default open https://gmail.com
agent-browser --profile "Work" open https://app.example.com
```

### Persistent Profile
```bash
agent-browser --profile ~/.myapp-profile open myapp.com
```

### Session Persistence
```bash
agent-browser --session-name twitter open twitter.com
# State auto-saved to ~/.agent-browser/sessions/
```

### Auth Vault (encrypted credentials)
```bash
echo "pass" | agent-browser auth save github --url https://github.com/login --username user --password-stdin
agent-browser auth login github
```

### Import from Running Chrome
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222
agent-browser --auto-connect state save ./my-auth.json
agent-browser --state ./my-auth.json open https://app.example.com/dashboard
```

## Security Features

```bash
agent-browser --content-boundaries open url        # Wrap output in boundary markers
agent-browser --allowed-domains "example.com,*.example.com" open url  # Domain allowlist
agent-browser --action-policy ./policy.json open url   # Gate destructive actions
agent-browser --confirm-actions eval,download open url  # Require approval
agent-browser --max-output 50000 open url          # Truncate output
```

## Cloud Providers

```bash
# Browserless
BROWSERLESS_API_KEY="token" agent-browser -p browserless open url

# Browserbase
BROWSERBASE_API_KEY="key" agent-browser -p browserbase open url

# Browser Use
BROWSER_USE_API_KEY="key" agent-browser -p browseruse open url

# Kernel
KERNEL_API_KEY="key" agent-browser -p kernel open url

# AWS AgentCore
agent-browser -p agentcore open url

# iOS Simulator
agent-browser -p ios --device "iPhone 16 Pro" open url
```

## MCP Server

```bash
agent-browser mcp                     # Start MCP stdio server (core tools)
agent-browser mcp --tools all         # Full typed CLI parity
agent-browser mcp --tools core,network,react  # Combined profiles
```

MCP profiles: `core`, `network`, `state`, `debug`, `tabs`, `react`, `mobile`, `all`

Example MCP client config:
```json
{
  "mcpServers": {
    "agent-browser": {
      "command": "agent-browser",
      "args": ["mcp"]
    }
  }
}
```

## Skills
```bash
agent-browser skills                  # List available skills
agent-browser skills get <name>       # Output a skill's full content
agent-browser skills get --all        # Output every skill
```

## Setup & Diagnostics
```bash
agent-browser install                 # Download Chrome
agent-browser install --with-deps     # Also install system deps (Linux)
agent-browser upgrade                 # Upgrade to latest
agent-browser doctor                  # Diagnose install and auto-clean stale daemon files
agent-browser doctor --fix            # Also run destructive repairs
```

## JSON Output (for agents)

Add `--json` for machine-readable output:
```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
agent-browser screenshot --json
```

## Configuration

Create `agent-browser.json` for persistent defaults:

Locations (lowest to highest priority):
1. `~/.agent-browser/config.json`: user-level defaults
2. `./agent-browser.json`: project-level overrides
3. `AGENT_BROWSER_*` environment variables
4. CLI flags override everything

```json
{
  "$schema": "https://agent-browser.dev/schema.json",
  "headed": true,
  "proxy": "http://localhost:8080",
  "profile": "./browser-data",
  "userAgent": "my-agent/1.0",
  "hideScrollbars": false,
  "ignoreHttpsErrors": true
}
```

## Options

| Option | Description |
|--------|-------------|
| `--session <name>` | Isolated session |
| `--session-name <name>` | Auto-save/restore session state |
| `--profile <name\|path>` | Chrome profile name or persistent directory |
| `--state <path>` | Load storage state from JSON |
| `--headed` | Show browser window |
| `--cdp <port\|url>` | Connect via CDP |
| `--auto-connect` | Auto-discover running Chrome |
| `--proxy <url>` | Proxy server |
| `--ignore-https-errors` | Ignore cert errors |
| `--allow-file-access` | Allow file:// URLs |
| `--json` | JSON output |
| `--annotate` | Annotated screenshots |
| `--config <path>` | Custom config file |
| `-v`, `--verbose` | Verbose output |
| `-q`, `--quiet` | Quiet mode |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AGENT_BROWSER_SESSION` | Session name |
| `AGENT_BROWSER_SESSION_NAME` | Auto-save/restore session |
| `AGENT_BROWSER_PROFILE` | Chrome profile |
| `AGENT_BROWSER_STATE` | State file path |
| `AGENT_BROWSER_EXECUTABLE_PATH` | Custom browser |
| `AGENT_BROWSER_PROXY` | Proxy URL |
| `AGENT_BROWSER_HEADED` | Show window |
| `AGENT_BROWSER_AUTO_CONNECT` | Auto-discover Chrome |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | Default timeout (ms, default: 25000) |
| `AGENT_BROWSER_IDLE_TIMEOUT_MS` | Auto-shutdown daemon after idle |
| `AGENT_BROWSER_CONTENT_BOUNDARIES` | Wrap output in boundaries |
| `AGENT_BROWSER_MAX_OUTPUT` | Max output chars |
| `AGENT_BROWSER_ALLOWED_DOMAINS` | Domain allowlist |
| `AGENT_BROWSER_ENCRYPTION_KEY` | AES-256-GCM key for state encryption |

## Example: Form submission

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## Example: Authentication with saved state

```bash
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Later: load saved state
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

## Example: Command chaining

```bash
# Open, wait, and snapshot in one call
agent-browser open example.com && agent-browser wait --load networkidle && agent-browser snapshot -i

# Chain multiple interactions
agent-browser fill @e1 "user@example.com" && agent-browser fill @e2 "pass" && agent-browser click @e3
```

## Selectors

### Refs (Recommended for AI)
Refs provide deterministic element selection from snapshots. Use `@e1`, `@e2`, etc.

### CSS Selectors
```bash
agent-browser click "#id"
agent-browser click ".class"
agent-browser click "div > button"
```

### Text & XPath
```bash
agent-browser click "text=Submit"
agent-browser click "xpath=//button"
```

## Platforms

| Platform | Binary |
|----------|--------|
| macOS ARM64 | Native Rust |
| macOS x64 | Native Rust |
| Linux ARM64 | Native Rust |
| Linux x64 | Native Rust |
| Windows x64 | Native Rust |

## Architecture

- **Rust CLI** - Parses commands, communicates with daemon
- **Rust Daemon** - Pure Rust daemon using direct CDP, no Node.js required
- **Browser Engine** - Chrome (from Chrome for Testing) by default; `--engine lightpanda` also supported

The daemon starts automatically on first command and persists between commands. Set `AGENT_BROWSER_IDLE_TIMEOUT_MS` for auto-shutdown after inactivity.

## License

Apache-2.0
