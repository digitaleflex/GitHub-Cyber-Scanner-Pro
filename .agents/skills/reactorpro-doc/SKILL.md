---
description: Comprehensive ReactorPro documentation covering installation, features, agent mode, configuration, skills, MCP servers, and all capabilities. Use this skill when answering questions about ReactorPro features, configuration, troubleshooting, or best practices.
name: reactorpro-doc
---

# ReactorPro Documentation Skill

This skill provides comprehensive documentation for ReactorPro, enabling you to answer questions about its features, configuration, and usage.

## Introduction

ReactorPro supercharges your coding workflow by combining the power of [aider](https://aider.chat) with an intuitive desktop interface, enabling seamless AI-assisted code generation, modification, and project management.

### Installation

1. **Download** the latest version for your operating system from the [Releases page](https://github.com/hotovo/aider-desk/releases)
2. **Install** the application:
   - **Windows**: Run the `.exe` installer
   - **macOS**: Open the `.dmg` and drag ReactorPro to Applications
   - **Linux**: Extract the `.AppImage` and make it executable (`chmod +x`)

### First Launch Experience

When you first open ReactorPro:
- The app will automatically set up required Python dependencies
- Create default configuration files in `~/.reactorpro`
- Open the main interface with a welcome screen

### Key Features

- **AI-Powered Coding**: Generate new code from natural language, modify existing code with precise edits, get explanations for complex code
- **Project Context Management**: Manual or automatic file inclusion, IDE plugins for VSCode and IntelliJ, read-only mode for reference files
- **Workflow Tools**: Session persistence, cost tracking per project, multiple AI provider support, built-in diff viewer with side-by-side comparison

---

## Chat Modes

ReactorPro offers several chat modes to tailor the AI's behavior to your specific needs:

### Code Mode (`/code`)
The default mode for direct interaction with Aider to request code changes. Best for specific, well-defined tasks.

### Agent Mode (`/agent`)
Activates the autonomous agent. Use for high-level, complex tasks that may require multiple steps, reasoning, and tool use.

### Ask Mode (`/ask`)
Ask questions about your codebase without the AI attempting to make any changes.

### Architect Mode (`/architect`)
A specialized mode for planning and executing large-scale changes affecting multiple files. The AI creates a plan first, then uses an "editor" model to apply changes.

### Context Mode (`/context`)
Aider will automatically analyze your prompt and try to identify and add the most relevant files to the context.

---

## Model Library

The Model Library is ReactorPro's advanced provider and model management system.

### Features
- **Multiple Provider Profiles**: Create multiple profiles for the same provider with different configurations
- **Custom Model Management**: Add models that aren't automatically discovered
- **Cost and Token Configuration**: Set custom pricing and token limits
- **Model Organization**: Hide irrelevant models and organize by provider profiles
- **Dynamic Model Loading**: Automatically discover available models for most providers

### Accessing the Model Library
1. **Top Bar Icon**: Click the Model Library icon in the top bar
2. **Model Selector**: Cog icon right from model selector
3. **Onboarding**: During initial setup

---

## Built-in Commands

### Core Commands
- `/add <files>`: Adds files to the chat context
- `/drop <files>`: Removes files from the context
- `/read-only <files>`: Adds files in read-only mode
- `/run <command>`: Executes a shell command
- `/test`: Runs the predefined test command

### Chat & Context Management
- `/clear`: Clears the entire chat history and drops all files
- `/clear-logs`: Removes only log messages
- `/compact`: Summarizes the conversation to reduce token usage
- `/copy-context`: Copies context to clipboard in markdown format
- `/tokens`: Reports token usage

### Mode Switching
- `/code`: Switch to Code Mode
- `/agent`: Switch to Agent Mode
- `/ask`: Switch to Ask Mode
- `/architect`: Switch to Architect Mode
- `/context`: Switch to Context Mode

### Model & Aider Control
- `/model <name>`: Changes the AI model
- `/reasoning-effort <level>`: Sets reasoning effort (low, medium, high)
- `/think-tokens <budget>`: Sets thinking token budget
- `/undo`: Undoes the last git commit
- `/redo`: Re-runs the last prompt
- `/edit-last`: Edit and re-submit last message

### Other Utilities
- `/web <url>`: Scrapes URL content and adds to chat
- `/map`: Prints the repository map
- `/map-refresh`: Forces refresh of repository map
- `/commit`: Commits unstaged changes
- `/resolve-conflicts`: Resolves merge conflicts using AI
- `/init`: Initializes AGENTS.md rule file
- `/handoff <focus>`: Extract context and create new focused task

---

## IDE Integration

### Visual Studio Code
- **Extension**: [ReactorPro Connector on Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=hotovo-sk.reactorpro-connector)
- Automatically adds the currently active file to ReactorPro context

### IntelliJ IDEA (and other JetBrains IDEs)
- **Plugin**: [ReactorPro Connector on JetBrains Marketplace](https://plugins.jetbrains.com/plugin/26313-ReactorPro-connector)
- Compatible with WebStorm, PyCharm, GoLand, and more

---

## Task Management

Tasks are containers for all the context, conversations, and decisions related to a specific piece of work.

### Task Organization
Tasks are stored in `.reactorpro/tasks/{taskId}/` with:
- `settings.json`: Task metadata and configuration
- `context.json`: Messages and files context
- `todos.json`: Todo items for the task

### Working Modes
- **Local Mode**: Work directly in main project directory
- **Worktree Mode**: Create isolated Git worktree for safe experimentation

### Subtasks
Break down complex work into hierarchical structures. Subtasks inherit parent's worktree path.

### Smart Task States
- **TODO**: Task hasn't been started yet
- **IN PROGRESS**: Task is currently being worked on
- **INTERRUPTED**: Task was stopped before completion
- **MORE INFO NEEDED**: Agent needs clarification
- **READY FOR IMPLEMENTATION**: Agent has a clear plan
- **READY FOR REVIEW**: Agent completed work, ready for human review
- **DONE**: Task marked as completed

### Task Operations
- **Rename**: Change task name
- **Duplicate**: Create complete copy
- **Delete**: Remove permanently
- **Archive**: Hide from main view
- **Pin**: Pin to top of list
- **Export**: Export as Markdown or PNG

---

## Git Worktrees

Git worktrees enable isolated development environments for each task.

### Integration Options
1. **Standard Merge**: Preserves all individual commits
2. **Squash & Merge**: Creates one clean commit
3. **Only Uncommitted Changes**: Transfers work-in-progress without commits

### Features
- AI-assisted conflict resolution
- Visual status indicators (ahead commits, uncommitted files)
- Rebase operations with conflict handling
- Revert operations for safety

---

## Custom Commands

Create custom commands in Markdown files with YAML front matter.

### Locations
- **Global**: `~/.reactorpro/commands/`
- **Project-specific**: `.reactorpro/commands/`

### Format
```yaml
---
description: A brief description of what the command does.
arguments:
  - description: Description for the first argument.
    required: true
---
Template content using {{1}}, {{2}}, or {{ARGUMENTS}} placeholders.
Lines starting with ! are executed as shell commands.
```

---

## Memory

ReactorPro Memory lets the agent store and retrieve durable, project-scoped knowledge across tasks.

### Prerequisites
1. Enable Memory in Settings: `Settings → Memory → Enabled`
2. Enable Memory tools for agent profile: `Settings → Agent → Use Memory Tools`

### Memory Tools
- `retrieve_memory`: Search for relevant memories
- `store_memory`: Save a new memory
- `list_memories`: List stored memories
- `delete_memory`: Delete a specific memory

### What to Store
- User preferences (formatting, frameworks, naming)
- Architectural decisions
- Reusable codebase patterns

### What NOT to Store
- One-off task status updates
- Temporary debugging notes
- Long logs/stack traces
- Secrets, tokens, credentials, or personal data

---

## Skills

Skills let you extend the agent with reusable, on-demand expertise. A skill is a folder containing instructions (and optionally scripts and reference materials).

### Where Skills Live
- **Home-level skills**: `~/.reactorpro/skills/`
- **Project-level skills**: `.reactorpro/skills/`

### Skill Structure
```
{skills-root}/
  {skill-name}/
    SKILL.md
    references/
    scripts/
    ...
```

### Prerequisites
Skills only work when **Skills Tools are enabled** for the active agent profile:
1. `Settings → Agent → Use Skills Tools`
2. Or via `AgentSelector → Use skills tools`

### Skills Tools
- **Discover installed skills** (using skill metadata)
- **Activate a skill** when relevant by loading its SKILL.md

---

## Hooks

Hooks allow you to extend ReactorPro's behavior by executing custom JavaScript code.

### Locations
- **Global**: `~/.reactorpro/hooks/`
- **Project-specific**: `.reactorpro/hooks/`

### Format
```javascript
module.exports = {
  onTaskCreated: async (event, context) => {
    context.addInfoMessage(`Task "${event.task.name}" was created!`);
  },
  onPromptStarted: async (event, context) => {
    if (event.prompt.includes('secret')) {
      return false; // Block the action
    }
  }
};
```

### Available Events
- `onTaskCreated`, `onTaskInitialized`, `onTaskClosed`
- `onPromptSubmitted`, `onPromptStarted`, `onPromptFinished`
- `onAgentStarted`, `onAgentFinished`, `onAgentStepFinished`
- `onToolCalled`, `onToolFinished`
- `onFileAdded`, `onFileDropped`
- `onCommandExecuted`
- `onAiderPromptStarted`, `onAiderPromptFinished`
- `onQuestionAsked`, `onQuestionAnswered`
- `onHandleApproval`
- `onSubagentStarted`, `onSubagentFinished`
- `onResponseMessageProcessed`

---

## Web Scraping

Use the `/web` command to pull content from any URL into your chat context.

### Usage
```
/web https://react.dev/reference/react/useState
```

### How It Works
1. Launches internal browser using Electron
2. Navigates and extracts raw HTML
3. Cleans and converts to markdown-like text
4. Saves to `.reactorpro/tmp` as read-only context file

---

## Voice Control

Voice Control allows speech-to-text functionality to dictate prompts.

### Supported Providers
- **OpenAI**: Uses OpenAI's real-time speech-to-text API
- **Google Gemini**: Uses Gemini's live audio input capabilities

### Setup
1. Configure provider profile with API key in Model Library
2. Enable Voice Control in Model Library provider settings
3. Configure voice options in `Settings → Voice`

---

## Handoff Command

The `/handoff` command extracts relevant context from your current conversation and moves it into a new, focused task.

### Usage
```
/handoff [your focus here]
```

### Examples
```
/handoff implement this for teams as well, not just individual users
/handoff execute phase one of the created plan
/handoff check the rest of the codebase and find other places that need this fix
```

### Handoff vs Compaction
- **Handoff**: Creates new focused task, preserves original conversation
- **Compact**: Summarizes and replaces current thread

---

## Compact Conversation

The `/compact` command summarizes your conversation history to reduce token usage.

### What It Does
- Generates structured summary including:
  - Primary request and overall intent
  - Key technical concepts
  - Chronological list of user messages
  - Files and code sections read/created/modified
  - Errors encountered and resolutions
  - Current work and next steps

---

## Usage Dashboard

Track usage patterns, token consumption, and costs across projects.

### Key Features
- **Activity Analysis**: Monitor development activity over time
- **Token Visualization**: Track consumption trends
- **Cost Breakdown**: By project and model
- **Interactive Patterns**: Filter by date, project, model

### View Modes
- **Table View**: Structured tabular format
- **Charts View**: Interactive visualizations

---

## ReactorPro as MCP Server

ReactorPro includes a built-in MCP server for other MCP-compatible clients.

### Available Tools via MCP
- `add_context_file`: Add file to context
- `drop_context_file`: Remove file from context
- `get_context_files`: List files in context
- `get_addable_files`: List available project files
- `run_prompt`: Execute a prompt
- `clear_context`: Clear the context

---

## Agent Mode

Agent Mode transforms ReactorPro into a powerful, autonomous assistant.

### Key Capabilities
- **Autonomous Task Execution**: Break down high-level requests into concrete steps
- **Tool Utilization**: Power Tools, Aider Tools, MCP Servers
- **Configurable Profiles**: Tailor behavior for different tasks
- **Transparent Operation**: Observe thought process and tool choices

### Switching to Agent Mode
1. Click mode selector below prompt field and choose "Agent"
2. Or type `/agent` in the prompt field

---

## Agent Profiles

Agent Profiles configure the agent's behavior. Create multiple profiles for different workflows.

### File-Based Storage
- **Global Profiles**: `~/.reactorpro/agents/`
- **Project-Level Profiles**: `$projectDir/.reactorpro/agents/`

### Profile Structure
```
profile-name/
├── config.json          # Profile configuration
└── rules/               # Additional rule files
    ├── coding-standards.md
    ├── architecture.md
    └── custom-instructions.md
```

### Pre-defined Profiles
1. **Power Tools**: Direct file system access for analysis and modification
2. **Aider**: Leverages Aider's code generation capabilities
3. **Aider with Power Search**: Combines search capabilities with Aider

### Configuration Options
- **Parameters**: Temperature, Max Iterations, Max Tokens, Min Time Between Tool Calls
- **Context Settings**: Include Context Files, Include Repository Map
- **Tool Groups**: Power Tools, Aider Tools, Todo Tools
- **Rules & Instructions**: Custom instructions and rule files
- **MCP Servers**: External tool connections
- **Tool Approvals**: Ask, Always, Never

---

## Subagents

Subagents are specialized AI assistants that can be delegated specific tasks.

### Key Benefits
- **Context Preservation**: Focused context without polluting main conversation
- **Specialized Expertise**: Domain-specific system prompts
- **Reusability**: Use across different projects
- **Flexible Permissions**: Different tool access levels
- **Cost Optimization**: Strategic model selection per task type

### Configuration
- **Enable as Subagent**: Toggle in agent profile
- **System Prompt**: Define behavior and expertise
- **Invocation Mode**: Automatic or On-demand
- **Color**: Visual identifier
- **Description**: When the subagent should be used

---

## Aider Tools

When Agent Mode is active, the agent can interact with Aider:

- `get_context_files`: List files in Aider's context
- `add_context_files`: Add files to context
- `drop_context_files`: Remove files from context
- `run_prompt`: Delegate a coding task to Aider

---

## Power Tools

Power tools provide direct file system interaction and development operations.

### File Operations
- `power---file_read`: Read file content
- `power---file_write`: Create/modify files (overwrite, append, create_only modes)
- `power---file_edit`: Targeted find-and-replace changes

### Search and Discovery
- `power---semantic_search`: Natural language code search
- `power---glob`: Find files using glob patterns
- `power---grep`: Search content with regex

### System Operations
- `power---bash`: Execute shell commands
- `power---agent`: Delegate to specialized sub-agents

### Tool Approval States
- **Ask**: Prompt for approval each time
- **Always**: Auto-approve without prompting
- **Never**: Disable the tool completely

---

## Task Tools

Task tools enable agents to interact with the task management system.

### Available Tools
- `tasks---list_tasks`: List all tasks in current project
- `tasks---get_task`: Get comprehensive task details
- `tasks---get_task_message`: Retrieve specific message from task history
- `tasks---create_task`: Create new task or subtask
- `tasks---delete_task`: Permanently delete a task
- `tasks---search_task`: Semantic search within a task
- `tasks---search_parent_task`: Search parent task content (for subtasks)

---

## MCP Servers

Extend Agent Mode with external tools through the Model Context Protocol.

### Configuration Format
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### Directory Placeholders
- `${projectDir}`: Project root directory
- `${taskDir}`: Current task's working directory

---

## AGENTS.md with /init

The `/init` command analyzes your codebase and generates an `AGENTS.md` file.

### What It Does
- Identifies project purpose and architecture
- Documents programming languages and frameworks
- Lists core dependencies and libraries
- Records coding conventions and patterns
- Documents build and testing procedures

### Usage
1. Switch to Agent Mode
2. Type `/init` and press Enter
3. Add generated file to Aider's read-only context when prompted

---

## Todo Management

The agent can track and complete multi-step tasks.

### Todo Tools
- `set_items`: Creates or overwrites the todo list
- `get_items`: Reads current todo state
- `update_item_completion`: Marks items complete/incomplete
- `clear_items`: Clears all items

---

## Configuration

### Settings Overview

Access settings via the gear icon in the top-right corner.

#### General Tab
- Appearance (language, zoom, theme)
- Start Up behavior
- Notifications
- Prompt Behavior

#### Providers Tab
Manage API keys and connections for LLM providers.

#### Aider Tab
- Options: Command-line arguments for Aider
- Environment Variables: For Aider process
- Context: Control automatic rule file inclusion

#### Agent Tab
- Agent Profiles
- MCP Servers
- Tool Approvals

#### Memory Tab
- Enable/disable Memory
- Embedding model selection
- View and delete stored memories

---

## Providers Configuration

Supported providers:
- **Anthropic**: Claude models
- **OpenAI**: GPT models
- **Azure**: Azure OpenAI (requires manual model addition)
- **Gemini**: Google Gemini models
- **Vertex AI**: Google Cloud enterprise AI
- **GPUStack**: OpenAI-compatible GPU inference
- **Deepseek**: Coding-optimized models
- **Groq**: Ultra-fast inference
- **Bedrock**: AWS foundation models
- **Claude Agent SDK**: For Claude Code Pro/Max subscriptions
- **OpenAI Compatible**: Custom endpoints
- **Ollama**: Local open-source models
- **LM Studio**: Local models with GUI
- **OpenRouter**: Multiple providers via single API
- **Requesty**: Optimized routing and caching

---

## Aider Configuration

### Priority Order
1. ReactorPro UI settings
2. Command-line options in settings
3. `.env` in project directory
4. `.aider.conf.yml` in project directory
5. `.env` in home directory
6. `.aider.conf.yml` in home directory
7. System environment variables

### Aider Options
Pass command-line arguments in `Settings > Aider > Options`.

### Environment Variables
Set in `Settings > Aider > Environment Variables`.

---

## Project-Specific Rules

### Rule File Locations
1. **Project-Level**: `.reactorpro/rules/`
2. **Agent-Specific**: `.reactorpro/agents/{profile}/rules/`
3. **Global**: `~/.reactorpro/agents/{profile}/rules/`

### Rule Precedence
1. Global agent rules
2. Project-level rules
3. Project agent rules

### What to Include
- Architecture overview
- Coding conventions
- Technology stack
- Do's and Don'ts
- Agent behavior guidelines
- Tool usage preferences

---

## Custom Prompts

ReactorPro uses Handlebars templates for AI agent behavior.

### Available Templates
- `system-prompt.hbs`: Main system prompt
- `init-project.hbs`: Project initialization
- `workflow.hbs`: Agent workflow guidance
- `compact-conversation.hbs`: Conversation summarization
- `commit-message.hbs`: Git commit messages
- `task-name.hbs`: Task name generation
- `update-task-state.hbs`: Task state determination
- `conflict-resolution-system.hbs`: Conflict resolution system prompt
- `conflict-resolution.hbs`: Conflict resolution instructions
- `handoff.hbs`: Handoff prompt generation

### Template Override System
1. **Project-Specific** (highest): `$PROJECT_DIR/.reactorpro/prompts/`
2. **Global** (medium): `~/.reactorpro/prompts/`
3. **Default** (lowest): Bundled with ReactorPro

### Handlebars Helpers
- `{{equals value1 value2}}`: Check equality
- `{{not value}}`: Logical NOT
- `{{assign varName value}}`: Assign variable
- `{{increment varName}}`: Increment variable
- `{{indent text spaces}}`: Indent text
- `{{cdata text}}`: Wrap in CDATA

---

## Troubleshooting

### Common Issues

**Microphone Not Working (Voice Control)**
1. Check microphone connection
2. Verify permissions
3. Select specific microphone in Settings
4. Ensure no other app is using it

**Power tools not available**
1. Check "Use Power Tools" is enabled
2. Verify agent profile configuration
3. Restart ReactorPro

**Skills not loading**
1. Verify Skills Tools are enabled for agent profile
2. Check skill is in correct directory
3. Ensure SKILL.md exists with proper frontmatter

**Memory not working**
1. Enable Memory in Settings
2. Enable Memory Tools for agent profile
3. Check embedding model is configured

---

## Best Practices

### Task Management
- Use descriptive task names
- Keep tasks focused on single features/bugs
- Archive completed tasks
- Use subtasks for large features

### Agent Profiles
- Create specialized profiles for different task types
- Use conservative approval settings initially
- Start with predefined profiles and customize
- Document custom configurations

### Skills
- Keep skill descriptions specific and action-oriented
- Prefer small, composable skills
- Move rarely-needed details to references/ directory
- Only install skills from trusted sources

### Memory
- Retrieve memories at task start
- Store reusable preferences and patterns
- Don't store task-specific or sensitive information

---

## Resources

- **GitHub Repository**: https://github.com/hotovo/aider-desk
- **Documentation**: https://ReactorPro.hotovo.com/docs/
- **VSCode Extension**: https://marketplace.visualstudio.com/items?itemName=hotovo-sk.reactorpro-connector
- **IntelliJ Plugin**: https://plugins.jetbrains.com/plugin/26313-ReactorPro-connector
