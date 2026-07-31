# agentsecrets project

> Create, link, and manage projects within the active workspace.

## Subcommands

```
agentsecrets project list
agentsecrets project create <name>
agentsecrets project use <project-id-or-name>
agentsecrets project update <name>
agentsecrets project delete <name>
agentsecrets project invite <email>
```

---

## Overview

A **project** maps to an application or service. Secrets are partitioned by project — `my-backend`, `mobile-app`, and `infra` can each have their own set of credentials.

Projects live inside workspaces. The active workspace determines which projects you can see and interact with.

When you run any `agentsecrets secrets` command, it reads the project context from `.agentsecrets/project.json` in the current directory.

---

## project list

```bash
agentsecrets project list
```

Lists all projects in the active workspace:

```
NAME             ID             CREATED
→ my-backend     proj_abc123    2026-01-15
  mobile-app     proj_def456    2026-02-01
  infra          proj_ghi789    2026-02-20
```

The `→` marks the project linked to the current directory (from `.agentsecrets/project.json`), if any.

---

## project create

```bash
agentsecrets project create my-backend
```

Creates a new project in the active workspace and links the current directory to it by writing `.agentsecrets/project.json`.

After this command:
```bash
agentsecrets status
# Project: my-backend (proj_abc123)
# Workspace: My Team (ws_xyz789)
# Storage: Keychain
```

One project per directory — running `project create` or `project use` in a directory overwrites the existing `.agentsecrets/project.json`.

---

## project use

```bash
agentsecrets project use my-backend
```

Links the current directory to an existing remote project. Writes `.agentsecrets/project.json`.

Use this when:
- A teammate created the project and you want to link your local directory to it
- You're switching a directory to a different project
- You cloned a repo that already has `.agentsecrets/project.json` and need to re-link

```bash
# Typical onboarding flow for a new team member:
git clone https://github.com/yourcompany/backend
cd backend
agentsecrets project use prod-backend
agentsecrets secrets pull
```

---

## project update

```bash
agentsecrets project update my-backend
```

Renames the project. Prompts interactively for the new name and description.

---

## project delete

```bash
agentsecrets project delete my-backend
```

Permanently deletes the project and all its secrets from the remote. This cannot be undone.

- Prompts for confirmation twice
- Severs the local `.agentsecrets/project.json` link if it matches the deleted project
- Does not delete secrets from the local keychain — run `agentsecrets secrets list` and delete manually if needed

*Requires: Admin or Owner role on the workspace.*

---

## project invite

```bash
agentsecrets project invite user@email.com
```

Invites a collaborator to the active project. This command handles the security boundary between personal and team work automatically.

### Personal Workspace Migration

If the project is currently in your **personal workspace**, AgentSecrets will automatically perform a "seamless migration" to a shared workspace during the invite:

1. **Creates a new shared workspace** with the same name as the project.
2. **Moves the project** from your personal workspace into this new shared workspace.
3. **Adds the invited user** and **yourself** as members of the new workspace.
4. **Re-encrypts all secrets** (development, staging, and production) with a new workspace-wide key that both members can access.

This ensures your personal workspace remains private, while allowing you to collaborate on specific projects as soon as you're ready to share them.

---

## The Project Config File

`.agentsecrets/project.json` is the link between a local directory and a remote project:

```json
{
  "project_id": "proj_abc123",
  "project_name": "my-backend",
  "description": "Production API services",
  "environment": "development",
  "workspace_id": "ws_xyz789",
  "workspace_name": "My Team",
  "last_pull": "2026-03-03T22:00:00Z",
  "last_push": "2026-03-03T21:00:00Z",
  "storage_mode": 1
}
```

**`project_id`** — the remote identifier used in all API calls  
**`storage_mode`** — `0` for `.env`, `1` for keychain  
**`last_pull` / `last_push`** — used by `agentsecrets secrets diff` to detect drift

This file contains no credentials and is safe to commit to version control. Teams can commit it so new developers just need to run `agentsecrets secrets pull` after cloning.

---

## Multi-Project Directories (Monorepos)

One directory = one active project. For monorepos, create a `.agentsecrets/project.json` in each service subdirectory. This allows each service to have its own secret namespace and environment context.

```
repo/
├── .agent/
│   └── workflows/
│       └── agentsecrets.md    # Shared agent instructions
├── services/
│   ├── api/
│   │   └── .agentsecrets/
│   │       └── project.json    # project: api-service
│   └── worker/
│       └── .agentsecrets/
│           └── project.json    # project: worker-service
└── ...
```

When you `cd` into a subdirectory, AgentSecrets automatically picks up the local project context.
