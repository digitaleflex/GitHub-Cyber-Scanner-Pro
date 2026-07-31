# agentsecrets proxy

> Manage local zero-knowledge proxy workflows for your AI agents.

## Usage

```bash
agentsecrets proxy <command> [flags]
```

## Description

The `proxy` commands manage the runtime connection between an AI agent and your APIs. It securely resolves keys from the OS keychain, intercepts outbound agent requests in real-time, applies zero-trust domain authorizations, and injects authentication headers without exposing values to the agent model.

## Available Commands

### `start`
Starts the HTTP credential proxy on your local machine (default port 8765).

```bash
agentsecrets proxy start [--port 9000]
```

### `status`
Displays the running status of your HTTP proxy, its uptime, process ID, the most recent background sync interval, and the volume of active/revoked identities that have been cached.

```bash
agentsecrets proxy status
```

### `sync`
Forces an immediate cryptographic revocation sync. If a teammate compromised or revoked a key globally, this instantly blocks your proxy from making outbound calls with it. Note that the proxy already auto-syncs periodically every 10 seconds.

```bash
agentsecrets proxy sync
```

### `logs`
Streams or views your proxy's local execution audit trail. This log structure definitively details memory-safe API interactions without displaying any raw secret content.

```bash
agentsecrets proxy logs                 # view entire log history
agentsecrets proxy logs --watch         # stream log outputs in real time
agentsecrets proxy logs --last N        # show last N entries
agentsecrets proxy logs --secret <key>  # filter logs associated to a local key
```
