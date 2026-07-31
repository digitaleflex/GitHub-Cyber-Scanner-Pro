#!/usr/bin/env python3
"""
Browser-Use Agent — AI-powered browser automation
Usage: python browser_agent.py "your task here"
  or: python browser_agent.py  (edit TASK below)
"""
import asyncio
import os
import sys

from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser

# Default task (override via CLI arg)
TASK = 'Go to google.com and search for the latest news about AI agents'

def get_llm():
    return ChatOpenAI(
        model='anthropic/claude-sonnet-4.6',
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY'),
    )

async def run(task: str, max_steps: int = 25, vision: bool = False):
    browser = Browser()
    llm = get_llm()
    agent = Agent(task=task, llm=llm, browser=browser, use_vision=vision)
    result = await agent.run(max_steps=max_steps)
    return result

def main():
    task = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else TASK
    max_steps = 25
    print(f"🌐 Browser-Use Agent")
    print(f"📋 Task: {task}")
    print(f"🤖 Model: anthropic/claude-sonnet-4.6 via OpenRouter")
    print(f"👁️  Vision: enabled (text-only model)")
    print(f"📏 Max steps: {max_steps}")
    print(f"─" * 50)
    
    result = asyncio.run(run(task, max_steps=max_steps, vision=True))
    
    print(f"─" * 50)
    print(f"✅ Result:")
    print(result.final_result())

if __name__ == '__main__':
    main()
