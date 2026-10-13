"""Fetch short advisory context from Tavily. Search results are untrusted text."""
import os

from dotenv import load_dotenv

load_dotenv()
MAX_CHARS_PER_RESULT = 700
MAX_RESULTS = 3


def fetch_context(finding):
    """Return (context_text, sources). Returns ('', []) if anything goes wrong."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return "", []
    try:
        from tavily import TavilyClient
        query = "how to fix and test for: " + finding[:200]
        res = TavilyClient(api_key=key).search(query, max_results=MAX_RESULTS)
        results = res.get("results", []) if isinstance(res, dict) else []
    except Exception as e:
        print("Tavily lookup failed:", type(e).__name__)
        return "", []
    parts, sources = [], []
    for r in results[:MAX_RESULTS]:
        text = (r.get("content") or "")[:MAX_CHARS_PER_RESULT]
        if text:
            parts.append(f"[{r.get('title', 'source')}] {text}")
            sources.append(r.get("url", ""))
    return "\n\n".join(parts), sources
