# Intro

Get started with OpenCode.

[**OpenCode**](https://opencode.ai/) is an open source AI coding agent. It's available as a terminal-based interface, desktop app, or IDE extension.

Let's get started.

---

## Prerequisites

To use OpenCode in your terminal, you'll need:

1. A modern terminal emulator like:
   - [WezTerm](https://wezterm.org/), cross-platform
   - [Alacritty](https://alacritty.org/), cross-platform
   - [Ghostty](https://ghostty.org/), Linux and macOS
   - [Kitty](https://sw.kovidgoyal.net/kitty/), Linux and macOS

2. API keys for the LLM providers you want to use.

---

## Install

The easiest way to install OpenCode is through the install script.

```bash
curl -fsSL https://opencode.ai/install | bash
```

You can also install it with the following commands:

### Using Node.js

```bash
npm install -g opencode-ai
# or
bun install -g opencode-ai
# or
pnpm install -g opencode-ai
# or
yarn global add opencode-ai
```

### Using Homebrew on macOS and Linux

```bash
brew install anomalyco/tap/opencode
```

> We recommend using the OpenCode tap for the most up to date releases. The official `brew install opencode` formula is maintained by the Homebrew team and is updated less frequently.

### Using Paru on Arch Linux

```bash
paru -S opencode-bin
```

### Windows

**Using Chocolatey:**
```bash
choco install opencode
```

**Using Scoop:**
```bash
scoop install opencode
```

**Using NPM:**
```bash
npm install -g opencode-ai
```

**Using Mise:**
```bash
mise use -g github:anomalyco/opencode
```

**Using Docker:**
```bash
docker run -it --rm ghcr.io/anomalyco/opencode
```

You can also grab the binary from the [Releases](https://github.com/anomalyco/opencode/releases).

---

## Configure

With OpenCode you can use any LLM provider by configuring their API keys.

If you are new to using LLM providers, we recommend using [OpenCode Zen](https://opencode.ai/docs/zen). It's a curated list of models that have been tested and verified by the OpenCode team.

1. Run the `/connect` command in the TUI, select opencode, and head to [opencode.ai/auth](https://opencode.ai/auth).

2. Sign in, add your billing details, and copy your API key.

3. Paste your API key.

Alternatively, you can select one of the other providers.

---

## Initialize

Now that you've configured a provider, you can navigate to a project that you want to work on.

```bash
cd /path/to/project
```

And run OpenCode.

```bash
opencode
```

Next, initialize OpenCode for the project by running the following command.

```
/init
```

This will get OpenCode to analyze your project and create an `AGENTS.md` file in the project root.

> **Tip:** You should commit your project's `AGENTS.md` file to Git.

This helps OpenCode understand the project structure and the coding patterns used.

---

## Usage

You are now ready to use OpenCode to work on your project. Feel free to ask it anything!

### Ask questions

You can ask OpenCode to explain the codebase to you.

> **Tip:** Use the `@` key to fuzzy search for files in the project.

```
How is authentication handled in @packages/functions/src/api/index.ts
```

This is helpful if there's a part of the codebase that you didn't work on.

### Add features

You can ask OpenCode to add new features to your project. Though we first recommend asking it to create a plan.

1. **Create a plan** - OpenCode has a *Plan mode* that disables its ability to make changes and instead suggest *how* it'll implement the feature. Switch to it using the **Tab** key.

2. **Iterate on the plan** - Once it gives you a plan, you can give it feedback or add more details.

3. **Build the feature** - Once you feel comfortable with the plan, switch back to *Build mode* by hitting the **Tab** key again.

### Make changes

For more straightforward changes, you can ask OpenCode to directly build it without having to review the plan first.

```
We need to add authentication to the /settings route. Take a look at how this is
handled in the /notes route in @packages/functions/src/notes.ts and implement
the same logic in @packages/functions/src/settings.ts
```

### Undo changes

Let's say you ask OpenCode to make some changes but you realize that it is not what you wanted. You **can undo** the changes using the `/undo` command.

```
/undo
```

OpenCode will now revert the changes you made and show your original message again.

> **Tip:** You can run `/undo` multiple times to undo multiple changes.

Or you **can redo** the changes using the `/redo` command.

```
/redo
```

---

## Share

The conversations that you have with OpenCode can be shared with your team.

```
/share
```

This will create a link to the current conversation and copy it to your clipboard.

> **Note:** Conversations are not shared by default.

---

## Customize

And that's it! You are now a pro at using OpenCode.

To make it your own, we recommend picking a theme, customizing the keybinds, configuring code formatters, creating custom commands, or playing around with the OpenCode config.
