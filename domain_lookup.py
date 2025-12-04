# domain_lookup.py
import requests
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ESGScraper/1.0)"
}

SEARCH_URL = "https://duckduckgo.com/html/"


def _extract_target_url(href: str) -> str | None:
    """
    DuckDuckGo often wraps results as:
    https://duckduckgo.com/l/?uddg=<encoded_target>&rut=...
    This function unwraps and returns the actual target URL.
    """
    parsed = urlparse(href)

    # If it's already an external site (not duckduckgo), just return it
    if "duckduckgo.com" not in parsed.netloc:
        return href

    # Try to decode ?uddg=<encoded_target>
    qs = parse_qs(parsed.query)
    if "uddg" in qs and qs["uddg"]:
        return unquote(qs["uddg"][0])

    return None


def lookup_domain(company_name: str, timeout: int = 10) -> str | None:
    """
    Use DuckDuckGo HTML search to guess the official domain for a company.
    Returns a URL like 'https://example.com' or None if nothing useful found.
    """
    query = f"{company_name} official site"
    params = {"q": query}

    try:
        resp = requests.get(SEARCH_URL, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Prefer links with the 'result__a' class (main results)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        target = _extract_target_url(href)
        if not target:
            continue

        parsed_target = urlparse(target)
        netloc = parsed_target.netloc
        if not netloc:
            continue

        # Ignore DuckDuckGo itself, take the first external domain
        if "duckduckgo.com" in netloc:
            continue

        # Normalize to https://<domain>
        return f"https://{netloc}"

    return None