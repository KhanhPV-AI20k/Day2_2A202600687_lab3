import os
import re
from typing import Optional

from dotenv import load_dotenv


MAX_RESULTS = 5
MAX_CONTENT_CHARS = 1200


def _get_tavily_api_key() -> Optional[str]:
    load_dotenv()
    return os.getenv("TAVILY_API_KEY")


def _create_tavily_client(api_key: str):
    from tavily import TavilyClient

    return TavilyClient(api_key=api_key)


def _trim_content(content: str) -> str:
    content = " ".join(content.split())
    if len(content) <= MAX_CONTENT_CHARS:
        return content
    return f"{content[:MAX_CONTENT_CHARS].rstrip()}..."


def _extract_url_content(url: str):
    api_key = _get_tavily_api_key()
    if not api_key:
        return None, "TAVILY_API_KEY is not set."

    try:
        client = _create_tavily_client(api_key)
        response = client.extract(urls=[url], include_images=False)
    except Exception as error:
        return None, str(error)

    results = response.get("results", [])
    if not results:
        return None, f"No Tavily page content found for {url}."

    content = results[0].get("raw_content") or ""
    if not content:
        return None, f"No Tavily page content found for {url}."

    return content, None


def _parse_title(content: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line
    return "Unknown"


def _parse_price(content: str) -> str:
    match = re.search(r"(?i)(?:price\s*:\s*)?(\$\s?\d[\d,]*(?:\.\d{2})?)", content)
    if match:
        return match.group(1).replace(" ", "")
    return "Unknown"


def _parse_availability(content: str) -> str:
    patterns = [
        r"(?i)\b(in stock|out of stock|sold out|available|unavailable|pre[- ]?order)\b",
        r"(?i)availability\s*:\s*([^\n.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    return "Unknown"


def search_web(query: str) -> str:
    query = query.strip()
    if not query:
        return "Tavily search error: query is empty."

    api_key = _get_tavily_api_key()
    if not api_key:
        return "Tavily search error: TAVILY_API_KEY is not set."

    try:
        client = _create_tavily_client(api_key)
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=MAX_RESULTS,
        )
    except Exception as error:
        return f"Tavily search error: {error}"

    results = response.get("results", [])
    if not results:
        return "No Tavily search results found."

    formatted_results = []
    for index, result in enumerate(results, start=1):
        title = result.get("title") or "Untitled"
        url = result.get("url") or "No URL"
        content = _trim_content(result.get("content") or "")
        formatted_results.append(
            f"Result {index}: {title}\nURL: {url}\nContent: {content}"
        )

    return "\n\n".join(formatted_results)


def browse_url(url: str) -> str:
    url = url.strip()
    if not url:
        return "Tavily extract error: URL is empty."

    content, error = _extract_url_content(url)
    if error:
        return f"Tavily extract error: {error}"

    return f"Page content for {url}:\n{_trim_content(content)}"


def extract_product_info(url: str) -> str:
    url = url.strip()
    if not url:
        return "Product extraction error: URL is empty."

    content, error = _extract_url_content(url)
    if error:
        return f"Product extraction error: {error}"

    return "\n".join(
        [
            f"Title: {_parse_title(content)}",
            f"Price: {_parse_price(content)}",
            f"Availability: {_parse_availability(content)}",
            f"URL: {url}",
            f"Evidence: {_trim_content(content)}",
        ]
    )
