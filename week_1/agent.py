import cycls
from openai import AsyncOpenAI

# Initialize agent for local development
agent = cycls.Agent()

# Initialize OpenAI client outside function (local development only)
client = AsyncOpenAI(api_key="")

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
    
    return await llm([system_message] + context.messages)

# Run locally
agent.run()