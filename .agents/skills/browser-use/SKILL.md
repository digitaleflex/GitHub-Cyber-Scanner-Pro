---
name: browser-use
description: AI browser automation agent — navigate websites, fill forms, extract data, click elements, search the web, take screenshots, download files, and automate any browser task using natural language. Uses anthropic/claude-sonnet-4.6 via OpenRouter with Playwright Chromium. Use when asked to browse websites, scrape data, fill web forms, automate repetitive browser tasks, search and extract information from web pages, or interact with any web application programmatically.
---

# Browser-Use

AI-powered browser automation. The agent sees the page, decides what to do, and acts — all from a natural language task description.

## Architecture

```
Task (natural language) → LLM (anthropic/claude-sonnet-4.6 via OpenRouter) → Action Plan
→ Playwright Chromium (headless) → DOM snapshot → LLM evaluates
→ Next action → ... → Done
```

## Quick Usage

### Basic agent (one-liner in Python)

```python
import asyncio
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser

llm = ChatOpenAI(
    model='anthropic/claude-sonnet-4.6',
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

agent = Agent(
    task='Go to hackernews and find the top 5 stories',
    llm=llm,
    use_vision=True,  # claude-sonnet-4.6 supports vision
)
agent.run_sync()
```

### With explicit browser config

```python
from browser_use import Agent, Browser, BrowserConfig

browser = Browser(config=BrowserConfig(
    headless=True,
    disable_security=True,
))

agent = Agent(
    task='Login to example.com with user x and pass y',
    llm=llm,
    browser=browser,
    use_vision=True,
)
await agent.run(max_steps=25)
```

## Model Configuration

The skill is pre-configured for **anthropic/claude-sonnet-4.6** via **OpenRouter**:

```python
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model='anthropic/claude-sonnet-4.6',
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),  # from scrt: openrouter/api_key
)
```

**Note**: `anthropic/claude-sonnet-4.6` supports vision. Set `use_vision=True` for screenshot-based browsing (recommended), or `use_vision=False` for text-only DOM mode (faster, cheaper).

### Switching models

```python
# For vision-capable models (GPT-4o, Claude Sonnet, etc.)
llm = ChatOpenAI(model='gpt-4o', base_url='https://openrouter.ai/api/v1', api_key=os.getenv('OPENROUTER_API_KEY'))
agent = Agent(task='...', llm=llm, use_vision=True)

# For Anthropic via native SDK
from browser_use import ChatAnthropic
llm = ChatAnthropic(model='claude-sonnet-4-6')
agent = Agent(task='...', llm=llm, use_vision=True)
```

## Agent Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | str | required | Natural language description of what to do |
| `llm` | BaseChatModel | required | LangChain-compatible LLM |
| `browser` | Browser | auto | Custom browser config (headless, proxy, etc.) |
| `use_vision` | bool | True | Enable screenshot-based vision (set False for text-only LLMs) |
| `max_steps` | int | 100 | Maximum action steps before stopping |
| `sensitive_data` | dict | None | Credentials the LLM references but never sees (see Security) |
| `controller` | Controller | default | Custom action registry |
| `flash_mode` | bool | False | Fast mode — skips planning, goes straight to action |
| `save_conversation_path` | str | None | Save full LLM conversation log to file |
| `initial_actions` | list | None | Actions to run before LLM takes over |

## Browser Options

```python
from browser_use import Browser, BrowserConfig

browser = Browser(config=BrowserConfig(
    headless=True,           # No visible window
    disable_security=True,   # Allow cross-origin iframes
    proxy="http://proxy:8080",  # HTTP/SOCKS proxy
    extra_chromium_args=[
        "--disable-blink-features=AutomationControlled",  # stealth
        "--window-size=1920,1080",
    ],
))
```

## Security: Sensitive Data

Never put passwords/API keys in the task text. Use `sensitive_data` instead:

```python
sensitive_data = {
    'https://example.com': {
        'username': 'actual_username',
        'password': 'actual_password',
    },
    'https://admin.portal.com': {
        'admin_email': 'admin@company.com',
        'admin_key': 'sk-xxxx',
    },
}

agent = Agent(
    task='Go to https://example.com and login with username and password',
    llm=llm,
    sensitive_data=sensitive_data,  # LLM sees "username"/"password" placeholders, never real values
)
```

The LLM references keys like `username` and `password` but never sees the actual values. The framework substitutes them at action time.

## Custom Actions

Register your own tools the agent can use:

```python
from browser_use import Controller

controller = Controller()

@controller.action('Save data to file')
def save_data(text: str, filename: str):
    with open(filename, 'w') as f:
        f.write(text)
    return f'Saved to {filename}'

@controller.action('Query database')
def query_db(sql: str):
    # connect to your DB and run sql
    return results

agent = Agent(
    task='Search for competitor pricing and save to prices.csv',
    llm=llm,
    controller=controller,
)
```

## Parallel Agents

Run multiple browser agents concurrently:

```python
agents = [
    Agent(task=f'Find the price of {item} on Amazon', llm=llm, browser=Browser())
    for item in ['laptop', 'phone', 'tablet']
]
results = await asyncio.gather(*[agent.run(max_steps=10) for agent in agents])
```

## Multi-Tab

```python
agent = Agent(
    task='Open 3 tabs: google.com, github.com, and stackoverflow.com. Search each for "python browser automation" and summarize results.',
    llm=llm,
)
```

## File Downloads

The agent can download files during browsing. Downloads go to the current working directory or a specified path:

```python
browser = Browser(config=BrowserConfig(
    downloads_path='/tmp/downloads',
))
```

## Common Task Patterns

### Web scraping
```python
agent = Agent(
    task='Go to https://news.ycombinator.com and extract the title, score, and URL of the top 10 stories. Return as JSON.',
    llm=llm, use_vision=True,
)
```

### Form filling
```python
agent = Agent(
    task='Go to https://httpbin.org/forms/post and fill in the form with name "Test User", email "test@example.com", and message "Hello from browser-use"',
    llm=llm, use_vision=True,
)
```

### Login + action
```python
sensitive_data = {'https://app.example.com': {'user': 'my@email.com', 'pass': '****'}}
agent = Agent(
    task='Go to https://app.example.com, login with user and pass, then go to the dashboard and find total revenue for this month',
    llm=llm, sensitive_data=sensitive_data, use_vision=True,
)
```

### Research
```python
agent = Agent(
    task='Search for "best open source SIEM tools 2026" and compile a comparison table with name, license, stars, and key features',
    llm=llm, use_vision=True, max_steps=25,
)
```

## Retrieving Results

```python
result = await agent.run(max_steps=10)

# Get the final text output
final = result.final_result()

# Get all action results
for action_result in result.all_results:
    print(action_result.extracted_content)

# Get the full model output history
for output in result.all_model_outputs:
    print(output)
```

## Script Template

Save this as a reusable script:

```python
#!/usr/bin/env python3
"""browser-use agent script — edit task and run"""
import asyncio, os
from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser

TASK = """EDIT THIS: Describe what you want the browser agent to do."""

llm = ChatOpenAI(
    model='anthropic/claude-sonnet-4.6',
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

async def main():
    browser = Browser()
    agent = Agent(task=TASK, llm=llm, browser=browser, use_vision=True)
    result = await agent.run(max_steps=25)
    print(result.final_result())

asyncio.run(main())
```

## Environment

- **Python**: >= 3.11
- **Node.js**: Not required (Playwright ships its own Chromium)
- **Chromium**: Auto-installed by `playwright install chromium`
- **API Key**: `OPENROUTER_API_KEY` env var (stored in scrt as `openrouter/api_key`)
- **Install**: `uv pip install browser-use langchain-openai`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ImportError: ChatOpenAI` | `uv pip install langchain-openai` |
| Chromium not found | `playwright install chromium` |
| OpenRouter 429 errors | Add retry logic or reduce `max_steps` |
| Agent loops on same action | Increase `max_steps` or rephrase task |
| Vision not working | Set `use_vision=True` explicitly |
| Cookie consent blocking | Add initial action to dismiss: `initial_actions=[{"click_element_by_index": {"index": 0}}]` |
