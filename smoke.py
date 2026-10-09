import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("NEBIUS_API_KEY")
print("Key found:", bool(key), "| length:", len(key) if key else 0)

client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=key)

print("\nNemotron models on your account:")
try:
    for m in client.models.list().data:
        if "nemotron" in m.id.lower():
            print(" ", m.id)
except Exception as e:
    print("Could not list models:", type(e).__name__, str(e)[:300])
