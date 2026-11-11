import httpx
from app.config import get_settings


class SearchError(RuntimeError):
    pass


async def web_search(query: str) -> list[dict]:
    """The agent's sole external tool: bounded, source-linked web search."""
    query = " ".join(query.split()).strip()
    if not query or len(query) > 400:
        raise ValueError("Search query must contain 1–400 characters.")
    settings = get_settings()
    if not settings.tavily_api_key:
        raise SearchError("TAVILY_API_KEY is not configured.")
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "fast",
        "max_results": 5,
        "include_answer": False,
        "include_raw_content": False,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.search_timeout_seconds) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SearchError(f"Web search failed: {exc}") from exc

    results = []
    for item in data.get("results", [])[:5]:
        url, title, content = item.get("url"), item.get("title"), item.get("content")
        if url and title and content:
            results.append({
                "title": str(title)[:300],
                "url": str(url)[:2000],
                "content": str(content)[:1800],
                "score": item.get("score"),
            })
    return results
