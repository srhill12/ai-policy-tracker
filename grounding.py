"""Source grounding: only URLs returned by the web search tool may be attached to an item."""

from urllib.parse import urlsplit, urlunsplit

PRIMARY_HOST_SUFFIXES = (".gov", ".mil")

VERIFIED = "Verified"
UNVERIFIED = "Unverified"


def normalize_url(url):
    """Comparison key for matching model-supplied URLs to search result URLs.

    Only differences that cannot change the target document are ignored:
    scheme/host case, a trailing slash, and the fragment.
    """
    if not isinstance(url, str):
        return None
    url = url.strip()
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return None
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def classify_source(url):
    host = (urlsplit(url).hostname or "").lower()
    return "primary" if host.endswith(PRIMARY_HOST_SUFFIXES) else "secondary"


def collect_search_results(content_blocks):
    """Map normalized URL to {url, title} for every result the web search tool returned."""
    results = {}
    for block in content_blocks:
        if getattr(block, "type", None) != "web_search_tool_result":
            continue
        content = getattr(block, "content", None)
        if not isinstance(content, list):
            continue
        for result in content:
            if getattr(result, "type", None) != "web_search_result":
                continue
            key = normalize_url(result.url)
            if key and key not in results:
                results[key] = {"url": result.url, "title": result.title}
    return results


def ground_items(raw_items, search_results):
    """Keep only model-cited URLs that appear in the search results.

    Each item gains: sources, source_type, verification, rejected_urls.
    Accepted URLs are replaced with the exact search result URL.
    """
    grounded = []
    for raw in raw_items:
        item = dict(raw)
        cited = item.pop("source_urls", None)
        item.pop("url", None)
        if isinstance(cited, str):
            cited = [cited]
        elif not isinstance(cited, list):
            cited = []

        sources, rejected, seen = [], [], set()
        for url in cited:
            key = normalize_url(url)
            match = search_results.get(key) if key else None
            if match is None:
                rejected.append(url)
            elif key not in seen:
                seen.add(key)
                sources.append({
                    "url": match["url"],
                    "title": match["title"],
                    "source_type": classify_source(match["url"]),
                })

        item["sources"] = sources
        item["rejected_urls"] = rejected
        if sources:
            item["verification"] = VERIFIED
            is_primary = any(s["source_type"] == "primary" for s in sources)
            item["source_type"] = "primary" if is_primary else "secondary"
        else:
            item["verification"] = UNVERIFIED
            item["source_type"] = None
        grounded.append(item)
    return grounded
