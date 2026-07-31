---
description: Remote system administration and shell execution through the OpenCode AI Server REST API for Windows, macOS, and Linux systems with full shell access, file operations, and process management
name: opencode-api
---

# OpenCode Remote Execution Skill

> **Autonomous System Administration Agent**  
> Full shell access and remote execution capabilities through the OpenCode AI Server REST API for Windows, macOS, and Linux systems.

## What I Do

I am a remote system administration skill that provides full access to execute shell commands and perform operations on connected systems through the OpenCode AI Server REST API. I enable:

- **Full Shell Access**: Execute any shell command on Windows (PowerShell/CMD/pwsh), macOS (zsh/bash), and Linux (bash/sh)
- **File System Operations**: Read, write, create, delete, and modify any files and directories
- **Process Management**: Start, stop, monitor, and manage system processes and services
- **Network Operations**: Configure networking, test connectivity, manage firewall rules
- **Software Management**: Install, update, remove applications and packages
- **System Configuration**: Modify system settings, environment variables, and configurations
- **Log Analysis**: Access and analyze system logs, event logs, and application logs
- **User Management**: Create, modify, and manage user accounts and permissions

## When to Use Me

Use this skill when you need to:

- Execute commands on remote Windows, macOS, or Linux systems
- Perform system administration tasks through REST API
- Automate multi-system operations
- Run health checks and diagnostics on remote servers
- Deploy or configure software remotely
- Access and manage files on remote systems
- Execute AI-assisted tasks on connected servers

## Server Configuration

```yaml
opencode_server:
  port: 9899
  base_url: "http://<hostname>:9899"
  endpoints:
    documentation: "/doc"
    shell: "/session/:id/shell"
    config: "/config"
  content_type: "application/json"
  timeout: 300
```

### Default Model Configuration

> **IMPORTANT**: Always use this exact model configuration for all API calls:

```json
{
  "model": {
    "providerID": "openrouter",
    "modelID": "anthropic/claude-opus-4.5"
  }
}
```

This is the **required** model configuration. Do not use other models.

## Recommended Approach: Send Message Endpoint

The most reliable method for executing tasks is using the `/session/:id/message` POST endpoint with AI assistance. This allows the AI to automatically execute commands and return structured results.

### Proven Working Pattern

```bash
# 1. Create session
SESSION=$(curl -s -X POST "http://<IP_ADDRESS>:9899/session" \
  -H "Content-Type: application/json" \
  -d '{"title":"Task Description"}' | jq -r '.id')

# 2. Send message with Claude Opus 4.5 (REQUIRED MODEL)
curl -s -X POST "http://<IP_ADDRESS>:9899/session/${SESSION}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": {"providerID": "openrouter", "modelID": "anthropic/claude-opus-4.5"},
    "parts": [{"type": "text", "text": "Your task description here"}]
  }'

# 3. Wait for processing (60-120 seconds for complex tasks)
sleep 90

# 4. Get results - check message count first
curl -s "http://<IP_ADDRESS>:9899/session/${SESSION}/message" | jq 'length'

# 5. Extract tool outputs from assistant message
curl -s "http://<IP_ADDRESS>:9899/session/${SESSION}/message" | jq -r '.[1].parts[].state.output'
```

### Response Structure

The AI response contains tool execution results in this structure:
```json
{
  "info": {"role": "assistant", "modelID": "anthropic/claude-opus-4.5", ...},
  "parts": [
    {"type": "step-start"},
    {"type": "tool", "tool": "bash", "state": {"status": "completed", "output": "..."}},
    {"type": "tool", "tool": "bash", "state": {"status": "completed", "output": "..."}},
    {"type": "step-finish"}
  ]
}
```

Extract results with: `jq -r '.[1].parts[].state.output'`

## API Endpoints

| Tool | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| `reference_api` | `/doc` | GET | Always reference API specification first |
| `get_config` | `/config` | GET | Retrieve server configuration |
| `create_session` | `/session` | POST | Create execution session |
| `list_sessions` | `/session` | GET | List all sessions |
| `get_session` | `/session/:id` | GET | Get session details |
| `delete_session` | `/session/:id` | DELETE | Remove session |
| `execute_shell` | `/session/:id/shell` | POST | Execute shell commands |
| `send_message` | `/session/:id/message` | POST | Send AI-assisted message |
| `get_messages` | `/session/:id/message` | GET | Retrieve session messages |
| `abort_session` | `/session/:id/abort` | POST | Abort running operation |
| `list_files` | `/file?path=<path>` | GET | List directory contents |
| `read_file` | `/file/content?path=<path>` | GET | Read file content |
| `search_files` | `/find?pattern=<pat>` | GET | Search for text patterns |
| `find_files` | `/find/file?query=<q>` | GET | Find files by name |

## Operational Protocol

### Phase 1: Initialize

**1. Reference API Documentation**
```bash
curl -s "http://<SERVER>:9899/doc"
```

**2. Verify Server Configuration**
```bash
curl -s "http://<SERVER>:9899/config" | jq .
```

**3. Create Execution Session**
```bash
curl -s -X POST "http://<SERVER>:9899/session" \
  -H "Content-Type: application/json" \
  -d '{"title":"Agent Execution Session"}'
```

### Phase 2: Execute

**4. Run Shell Commands**
```bash
curl -s -X POST "http://<SERVER>:9899/session/${SESSION_ID}/shell" \
  -H "Content-Type: application/json" \
  -d '{"agent":"default","command":"<COMMAND>"}'
```

### Phase 3: Retrieve

**5. Get Command Output**
```bash
curl -s "http://<SERVER>:9899/session/${SESSION_ID}/message" | jq .
```

### Phase 4: Cleanup (Optional)

**6. Delete Session**
```bash
curl -s -X DELETE "http://<SERVER>:9899/session/${SESSION_ID}"
```

## Tool Schemas

### execute_shell

```json
{
  "name": "execute_shell",
  "description": "Execute shell command on remote server",
  "endpoint": "/session/:id/shell",
  "method": "POST",
  "parameters": {
    "session_id": {
      "type": "string",
      "required": true,
      "description": "Active session ID"
    },
    "command": {
      "type": "string", 
      "required": true,
      "description": "Shell command to execute"
    },
    "agent": {
      "type": "string",
      "default": "default",
      "description": "Agent to use for execution"
    },
    "model": {
      "type": "object",
      "required": true,
      "properties": {
        "providerID": {"type": "string"},
        "modelID": {"type": "string"}
      }
    }
  }
}
```

### create_session

```json
{
  "name": "create_session",
  "description": "Create a new execution session",
  "endpoint": "/session",
  "method": "POST",
  "parameters": {
    "title": {
      "type": "string",
      "required": false,
      "description": "Session title for identification"
    },
    "parentID": {
      "type": "string",
      "required": false,
      "description": "Parent session ID for forking"
    }
  }
}
```

### send_message

```json
{
  "name": "send_message",
  "description": "Send AI-assisted message with context",
  "endpoint": "/session/:id/message",
  "method": "POST",
  "parameters": {
    "session_id": {
      "type": "string",
      "required": true
    },
    "parts": {
      "type": "array",
      "required": true,
      "items": {
        "type": {"type": "string", "enum": ["text", "image"]},
        "text": {"type": "string"}
      }
    },
    "model": {
      "type": "object",
      "required": true,
      "properties": {
        "providerID": {"type": "string"},
        "modelID": {"type": "string"}
      }
    }
  }
}
```

## Encoding Standards

### JSON Encoding (Required)

Always use `jq` for proper JSON escaping:
```bash
jq -n --arg cmd 'echo "Hello" && ls -la' '{agent: "default", command: $cmd}'
```

### URL Encoding

For query parameters with special characters:
```bash
ENCODED=$(printf '%s' "/path/with spaces" | jq -sRr @uri)
curl -s "http://<SERVER>:9899/file/content?path=${ENCODED}"
```

### Base64 Encoding (Complex Commands)

For multi-line or heavily escaped commands:
```bash
ENCODED_CMD=$(echo -n 'complex command' | base64)
COMMAND="echo $ENCODED_CMD | base64 -d | sh"
```

## Platform-Specific Commands

### Windows (PowerShell)

```json
{"agent": "default", "command": "pwsh -Command \"Get-Process\""}
{"agent": "default", "command": "pwsh -Command \"Get-Service | Where-Object {$_.Status -eq 'Running'}\""}
{"agent": "default", "command": "pwsh -Command \"Get-EventLog -LogName System -Newest 50\""}
{"agent": "default", "command": "pwsh -Command \"Get-PSDrive -PSProvider FileSystem\""}
{"agent": "default", "command": "pwsh -Command \"Get-NetTCPConnection -State Listen\""}
```

### macOS

```json
{"agent": "default", "command": "system_profiler SPSoftwareDataType SPHardwareDataType"}
{"agent": "default", "command": "df -h && free -m 2>/dev/null || vm_stat"}
{"agent": "default", "command": "ps aux | head -20"}
{"agent": "default", "command": "netstat -an | grep LISTEN"}
{"agent": "default", "command": "log show --predicate 'eventMessage contains \"error\"' --last 1h"}
{"agent": "default", "command": "launchctl list"}
```

### Linux

```json
{"agent": "default", "command": "uname -a && cat /etc/os-release"}
{"agent": "default", "command": "free -h && df -h"}
{"agent": "default", "command": "systemctl list-units --type=service --state=running"}
{"agent": "default", "command": "journalctl -p err --since '1 hour ago'"}
{"agent": "default", "command": "ss -tulpn"}
{"agent": "default", "command": "top -bn1 | head -20"}
```

## Execution Templates

### Template: System Health Check

```bash
#!/bin/bash
SERVER="http://<HOST>:9899"

# 1. Reference docs
curl -s "${SERVER}/doc" > /dev/null

# 2. Create session
SESSION_ID=$(curl -s -X POST "${SERVER}/session" \
  -H "Content-Type: application/json" \
  -d '{"title":"Health Check"}' | jq -r '.id')

# 3. Execute health commands
for CMD in "hostname" "uptime" "df -h" "free -h" "ps aux --sort=-%mem | head -10"; do
  curl -s -X POST "${SERVER}/session/${SESSION_ID}/shell" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg c "$CMD" '{agent:"default",command:$c}')"
done

# 4. Get results
curl -s "${SERVER}/session/${SESSION_ID}/message" | jq '.[] | .parts[] | .text'
```

### Template: Execute with AI Assistance (RECOMMENDED)

```bash
#!/bin/bash
# IMPORTANT: Always use Claude Opus 4.5 via OpenRouter
SERVER="http://<IP_ADDRESS>:9899"
TASK="$1"

# Create session
SESSION_ID=$(curl -s -X POST "${SERVER}/session" \
  -H "Content-Type: application/json" \
  -d '{"title":"AI Assisted Task"}' | jq -r '.id')

echo "Session: $SESSION_ID"

# Send message with REQUIRED model configuration
curl -s -X POST "${SERVER}/session/${SESSION_ID}/message" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg t "$TASK" '{
    model: {providerID: "openrouter", modelID: "anthropic/claude-opus-4.5"},
    parts: [{type: "text", text: $t}]
  }')" > /dev/null

# Wait for AI to process (adjust based on task complexity)
echo "Processing..."
sleep 90

# Check if response is ready (should be > 1 message)
MSG_COUNT=$(curl -s "${SERVER}/session/${SESSION_ID}/message" | jq 'length')
echo "Messages: $MSG_COUNT"

# Extract tool outputs
curl -s "${SERVER}/session/${SESSION_ID}/message" | jq -r '.[1].parts[] | select(.state.output) | .state.output'
```

### Template: Database Query via AI

```bash
#!/bin/bash
SERVER="http://<IP_ADDRESS>:9899"

SESSION=$(curl -s -X POST "${SERVER}/session" \
  -H "Content-Type: application/json" \
  -d '{"title":"Database Query"}' | jq -r '.id')

curl -s -X POST "${SERVER}/session/${SESSION}/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": {"providerID": "openrouter", "modelID": "anthropic/claude-opus-4.5"},
    "parts": [{"type": "text", "text": "Connect to MySQL database mydb on localhost:3306 with user admin password admin. Run: SELECT * FROM users LIMIT 10;"}]
  }' > /dev/null

sleep 60

# Get query results
curl -s "${SERVER}/session/${SESSION}/message" | jq -r '.[1].parts[] | select(.type=="tool") | .state.output'
```

## Error Handling

### Retry Logic

```bash
MAX_RETRIES=3
RETRY_DELAY=2

execute_with_retry() {
  local CMD="$1"
  local ATTEMPT=1
  
  while [ $ATTEMPT -le $MAX_RETRIES ]; do
    RESULT=$(curl -s -X POST "${SERVER}/session/${SESSION_ID}/shell" \
      -H "Content-Type: application/json" \
      -d "$(jq -n --arg c "$CMD" '{agent:"default",command:$c}')")
    
    if echo "$RESULT" | jq -e '.parts' > /dev/null 2>&1; then
      echo "$RESULT"
      return 0
    fi
    
    echo "Attempt $ATTEMPT failed, retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
    ATTEMPT=$((ATTEMPT + 1))
  done
  
  return 1
}
```

### Abort Stuck Operations

```bash
curl -s -X POST "${SERVER}/session/${SESSION_ID}/abort"
```

### Session Recovery

```bash
# List existing sessions
SESSIONS=$(curl -s "${SERVER}/session" | jq -r '.[].id')

# Reuse or cleanup
for SID in $SESSIONS; do
  STATUS=$(curl -s "${SERVER}/session/status" | jq -r ".\"${SID}\"")
  if [ "$STATUS" = "idle" ]; then
    SESSION_ID="$SID"
    break
  fi
done
```

## Security Directives

1. **Credential Handling**: Never log or expose credentials in command output
2. **Command Validation**: Validate destructive commands before execution
3. **Audit Trail**: All operations are logged via session messages
4. **Scope Limitation**: Operate only on designated target systems
5. **Privilege Escalation**: Use sudo/admin privileges only when necessary

## Permissions

```yaml
permissions:
  shell:
    execute: true
    sudo: true
    interactive: false
  filesystem:
    read: true
    write: true
    delete: true
    execute: true
  network:
    outbound: true
    inbound: true
    configure: true
  process:
    spawn: true
    kill: true
    monitor: true
  system:
    configure: true
    reboot: false
    shutdown: false
```

## Response Format

Structure responses as:

```
## Action Performed
<description>

## Commands Executed
<list of commands>

## Output
<command output>

## Status
Success | Warning | Error

## Next Steps (if applicable)
<recommendations>
```

## Quick Reference

```bash
# Reference API
curl -s http://<IP_ADDRESS>:9899/doc

# Create Session
curl -s -X POST http://<IP_ADDRESS>:9899/session -H "Content-Type: application/json" -d '{"title":"Session"}'

# Send AI Message (RECOMMENDED - use Claude Opus 4.5)
curl -s -X POST http://<IP_ADDRESS>:9899/session/<ID>/message \
  -H "Content-Type: application/json" \
  -d '{"model":{"providerID":"openrouter","modelID":"anthropic/claude-opus-4.5"},"parts":[{"type":"text","text":"<TASK>"}]}'

# Execute Shell (direct, no AI)
curl -s -X POST http://<IP_ADDRESS>:9899/session/<ID>/shell -H "Content-Type: application/json" -d '{"agent":"default","command":"<CMD>"}'

# Get Output (wait for processing first)
curl -s http://<IP_ADDRESS>:9899/session/<ID>/message | jq .

# Get Tool Results Only
curl -s http://<IP_ADDRESS>:9899/session/<ID>/message | jq -r '.[1].parts[] | select(.state.output) | .state.output'

# Check Message Count
curl -s http://<IP_ADDRESS>:9899/session/<ID>/message | jq 'length'

# Abort
curl -s -X POST http://<IP_ADDRESS>:9899/session/<ID>/abort

# Delete
curl -s -X DELETE http://<IP_ADDRESS>:9899/session/<ID>
```

## Critical Notes

1. **Always use Claude Opus 4.5**: `"providerID": "openrouter", "modelID": "anthropic/claude-opus-4.5"`
2. **Wait for processing**: Complex tasks may take 60-120+ seconds
3. **Check message count**: Response ready when `jq 'length'` returns > 1
4. **Extract tool outputs**: Results are in `.[1].parts[].state.output`
5. **Local server default**: `http://127.0.0.1:9899`

## Known Server Endpoints

| Server | URL | Platform |
|--------|-----|----------|
| Local macOS | http://127.0.0.1:9899 | macOS |
| AWS Windows 1 | http://44.197.31.152:9899 | Windows |
| AWS Windows 2 | http://52.3.242.251:9899 | Windows |

## Version Information

**Version:** 1.0  
**Last Updated:** 2026-01-11  
**Compatibility:** OpenCode Agent Skills Framework  
**Stack:** curl + REST API  
**Platforms:** Windows, macOS, Linux  
**API Version:** OpenCode Server v1.x

---

*This skill provides full remote execution capabilities. Always reference `/doc` endpoint before operations. All shell commands are executed through the `/session/:id/shell` endpoint with proper JSON encoding.*
