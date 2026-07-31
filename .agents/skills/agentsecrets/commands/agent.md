# agentsecrets agent

> Manage AI agent identities and their access tokens.

## Usage

```bash
agentsecrets agent <command> [flags]
```

## Description

The `agent` command lets you create and manage named identities for your AI agents. Once an agent has an identity, every credential call it makes is logged against that name, and you can revoke its access at any time without affecting other agents in the workspace.

## Available Commands

### `list`

Lists all agent identities in the current workspace.

```bash
agentsecrets agent list
```

### `delete`

Deletes an agent identity by name and revokes all of its active tokens.

```bash
agentsecrets agent delete "my-agent-name"
```

### `token issue`

Issues a new token for an existing agent identity.

```bash
agentsecrets agent token issue "my-agent-name"
```

### `token list`

Lists all active tokens for an agent.

```bash
agentsecrets agent token list "my-agent-name"
```

### `token revoke`

Revokes a specific token without deleting the agent identity.

```bash
agentsecrets agent token revoke "<token-id>" --agent="my-agent-name"
```