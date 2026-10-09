import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/",
                api_key=os.getenv("NEBIUS_API_KEY"))

MODELS = [
    "nvidia/Nemotron-3_5-Lightning",
    "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/Nemotron-3-Ultra-550b-a55b",
]

tools = [{
    "type": "function",
    "function": {
        "name": "run_tests",
        "description": "Run the project's test suite and return the result.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "test folder"}},
            "required": ["path"],
        },
    },
}]

for model in MODELS:
    print("\n==", model)
    try:
        r = client.chat.completions.create(
            model=model,
            max_tokens=1500,
            tools=tools,
            messages=[{"role": "user", "content": "Run the tests in the folder 'tests'."}],
        )
        msg = r.choices[0].message
        print("finish_reason:", r.choices[0].finish_reason)
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            print("TOOL CALL:", tc.function.name, tc.function.arguments)
        else:
            print("no tool call. content:", repr(msg.content)[:200])
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e)[:300])
