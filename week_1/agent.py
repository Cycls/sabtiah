import cycls
from openai import AsyncOpenAI
import re

import io
import traceback
from contextlib import redirect_stdout

def execute_python(code: str) -> str:
    """A more compact function to execute Python code and capture output."""
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, {})
        output = buffer.getvalue()
        # Use a ternary operator for a concise return statement
        return output
    except Exception:
        # traceback.format_exc() gives a full, detailed error report
        return f"--- Error during execution ---\n{traceback.format_exc()}"

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
    system_message = {
        "role": "system", 
        "content": (
            "You are an expert Python programmer. Your name is CoderBot. "
            "Your primary goal is to help users with their Python questions by providing clear explanations and writing clean, efficient code. "
            "When you provide Python code, you MUST always wrap it in a Markdown code block with the language identifier. "
            "For example: \n"
            "```python\n"
            "print('Hello, world!')\n"
            "```"
        )
    }
    full_messages = [system_message] + context.messages
    current_response = ""
    async for token in await llm(full_messages):
        current_response += token
        yield token

    yield "\n----\n\n"
    yield "# RESULT\n"
    yield execute_python(parse_python(current_response))

# Run locally
agent.run()