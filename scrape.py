# scrape.py
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import deque

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ESGScraper/1.0)"
}

ESG_KEYWORDS = [
    "sustainability", "esg", "responsibility", "impact",
    "environment", "governance", "social", "csr"
]


def _root_domain(url: str) -> str:
    """
    Get a simple root domain, e.g.:
      - https://www.netflix.com -> netflix.com
      - https://about.netflix.com -> netflix.com
      - https://corporate.apple.com -> apple.com
    Naive but fine for this project.
    """
    netloc = urlparse(url).netloc.lower()
    netloc = netloc.split(":")[0]
    parts = netloc.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return netloc


def is_same_domain(base_url: str, target_url: str) -> bool:
    """
    Consider subdomains as the same site.
    """
    return _root_domain(base_url) == _root_domain(target_url)


def looks_relevant(url: str, esg_only: bool = True) -> bool:
    """
    If esg_only is True, only follow URLs that look ESG-related.
    If esg_only is False, accept all same-root-domain URLs.
    """
    if not esg_only:
        return True

    url_lower = url.lower()
    return any(k in url_lower for k in ESG_KEYWORDS)


def fetch_html(url: str, timeout: int = 15) -> str:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    return "\n".join(lines)


def crawl_site(
    root_url: str,
    max_pages: int = 15,
    max_depth: int = 2,
    esg_only: bool = True,
) -> tuple[dict, list]:
    """
    Crawl starting from root_url.

    Returns:
        pages: dict[url -> clean_text]
        pdf_urls: list of ESG-ish PDF URLs found while crawling

    If esg_only=True, only follow ESG-related URLs (by path).
    If esg_only=False, follow all same-root-domain URLs.
    """
    visited = set()
    to_visit = deque()
    to_visit.append((root_url, 0))
    pages = {}
    pdf_urls = set()

    while to_visit and len(pages) < max_pages:
        url, depth = to_visit.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        try:
            html = fetch_html(url)
        except Exception:
            continue

        text = html_to_text(html)
        pages[url] = text

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(url, href)

            # Collect ESG-ish PDFs
            if full.lower().endswith(".pdf"):
                anchor_text = (a.get_text() or "").lower()
                full_lower = full.lower()
                if any(k in full_lower for k in ESG_KEYWORDS) or \
                   any(k in anchor_text for k in ESG_KEYWORDS + ["report", "annual", "impact"]):
                    pdf_urls.add(full)
                continue

            # Skip non-HTML links for crawling
            if not is_same_domain(root_url, full):
                continue
            if full in visited:
                continue
            if looks_relevant(full, esg_only=esg_only):
                to_visit.append((full, depth + 1))

    return pages, list(pdf_urls)