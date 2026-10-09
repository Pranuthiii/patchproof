import os
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

for model in MODELS:
    print("\n==", model)
    try:
        r = client.chat.completions.create(
            model=model,
            max_tokens=800,
            messages=[{"role": "user",
                       "content": 'Reply with only this JSON: {"action":"ping"}'}],
        )
        msg = r.choices[0].message
        reasoning = getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None)
        print("finish_reason:", r.choices[0].finish_reason)
        print("content:", repr(msg.content)[:200])
        print("has reasoning field:", bool(reasoning))
        print("tokens used:", r.usage.total_tokens)
    except Exception as e:
        print("ERROR:", type(e).__name__, str(e)[:300])
