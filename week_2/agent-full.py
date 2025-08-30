# generate a math agent that can help me understand math

# my api key:
# sk-...

# full code

import requests
import cycls
from openai import AsyncOpenAI
import re

import io
import traceback
from contextlib import redirect_stdout

import asyncio
import subprocess

def fetch_content(url):
  try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.text
  except requests.exceptions.RequestException as e:
    print(f"Error fetching content: {e}")
    return None

async def execute_python(code: str):
    """
    Executes Python code in a separate process and streams its combined
    output and errors in real-time. Much simpler.
    """
    # The '-u' flag forces python's output to be unbuffered.
    command = ["python", "-u", "-c", code]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        # This is the key simplification: merge stderr into stdout.
        stderr=subprocess.STDOUT 
    )

    yield "--- Subprocess started. Logs will appear below ---\n"

    # Now we only need to read from one stream (process.stdout).
    # The 'async for' loop handles everything automatically.
    if process.stdout:
        async for line_bytes in process.stdout:
            yield line_bytes.decode('utf-8')

    # Wait for the process to finish and get the exit code.
    await process.wait()
    
    yield f"\n--- Subprocess finished with exit code: {process.returncode} ---"

def parse_python(markdown_text):
    """Finds and extracts a Python code block from markdown text."""
    # Use re.search to find the pattern and a conditional expression to handle the result.
    match = re.search(r"```python\n(.*?)\n```", markdown_text, re.DOTALL)
    return match.group(1).strip() if match else "No Python code block was found."

# Initialize agent for local development
agent = cycls.Agent()

# Initialize OpenAI client outside function (local development only)
client = AsyncOpenAI(api_key="sk-...")

# Simple LLM function using OpenAI
async def llm(messages):
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        stream=True
    )
    
    # Stream the response
    async def event_stream():
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    
    return event_stream()

# Register your agent
@agent("my-agent")
async def my_agent(context):
    system_message = [{
        "role": "system", 
        "content": (
        "You are CyclsAgentArchitect, an expert AI specializing in creating Python agents using the `cycls` library.\n\n"
        "Your primary function is to write complete, functional Python code for new agents based on user requests. "
        "Your single most important directive is to adhere strictly to the patterns, functions, and best practices outlined in the provided `cycls` library documentation. "
        "Do not invent or hallucinate functionalities that are not present in the documentation.\n\n"
        "When a user asks you to create an agent, you must respond with:\n"
        "1.  A brief, one-sentence summary of the agent's purpose.\n"
        "2.  A single, self-contained Python code block that defines the new agent.\n\n"
        "The generated Python code MUST follow this exact structure:\n"
        "- Start with the `@agent(...)` decorator.\n"
        "- Define the agent as an `async def` function that accepts `context`.\n"
        "- Inside the function, create a `system_message` list of dictionaries. This list defines the persona and instructions for the *new* agent you are creating.\n"
        "- Combine your `system_message` with the user's input using `full_messages = system_message + context.messages`.\n"
        "- Use the `async for token in await llm(full_messages):` pattern to process the request and stream the response."
    )
    }, 
    {"role":"system", "content": "always include the llm function implementation if needed and use the following key: sk-..."},
    {"role":"system", "content": fetch_content("https://docs.cycls.com/llms-full.txt")}]
    full_messages = system_message + context.messages
    current_response = ""
    async for token in await llm(full_messages):
        current_response += token
        yield token

    yield "\n----\n\n"
    yield "# RESULT\n"
    # yield execute_python(parse_python(current_response))
    # print(parse_python(current_response))
    async for log_line in execute_python(parse_python(current_response)):
        yield log_line
        print(log_line, end='') 


# Run locally
agent.run(port=3000)