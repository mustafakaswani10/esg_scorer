# esg_search.py
import os
import requests
from scrape import DEFAULT_HEADERS

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

PDF_QUERY_TEMPLATES = [
    "{name} ESG report pdf",
    "{name} sustainability report pdf",
    "{name} impact report pdf",
    "{name} environmental report pdf",
    "{name} csr report pdf",
    "{name} ESG pdf",
    "{name} sustainability pdf",
    "{name} impact pdf",
]

HTML_QUERY_TEMPLATES = [
    "{name} ESG report",
    "{name} sustainability report",
    "{name} impact report",
    "{name} ESG sustainability",
    "{name} environmental social governance",
]

# Mixed E / S / G snippet queries
SNIPPET_QUERY_TEMPLATES = [
    # Environment-focused
    "{name} impact report climate targets net zero",
    "{name} sustainability report greenhouse gas emissions scope 1 and 2",
    "{name} sustainability report renewable energy usage",
    "{name} climate targets net zero emissions",

    # Social-focused
    "{name} diversity policy female leadership percentage",
    "{name} workforce diversity equity inclusion report",
    "{name} employee wellbeing and workplace safety programs",

    # Governance-focused
    "{name} corporate governance independent board ESG oversight",
    "{name} anti-corruption policy whistleblower mechanism",
    "{name} ESG governance structure board committee",
]

PDF_KEYWORDS = [
    "esg",
    "sustainability",
    "impact",
    "csr",
    "responsibility",
    "environmental",
    "report",
]


def _is_pdf(url: str) -> bool:
    return url.lower().endswith(".pdf")


def _looks_esg(url: str, title: str | None) -> bool:
    text = (url + " " + (title or "")).lower()
    return any(k in text for k in PDF_KEYWORDS)


def _serper_search(query: str) -> list[dict]:
    if not SERPER_API_KEY:
        return []

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
        **DEFAULT_HEADERS,
    }
    payload = {"q": query, "num": 10}

    try:
        resp = requests.post(SERPER_URL, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json().get("organic", []) or []
    except Exception:
        return []


def search_esg_pdfs(company_name: str, max_results: int = 5) -> list[str]:
    if not SERPER_API_KEY:
        print("  -> SERPER_API_KEY not set; skipping external ESG PDF search.")
        return []

    pdfs: list[str] = []

    for template in PDF_QUERY_TEMPLATES:
        query = template.format(name=company_name)
        print(f"    -> PDF query: {query}")
        results = _serper_search(query)

        for r in results:
            url = r.get("link")
            title = r.get("title")
            if not url:
                continue
            if not _is_pdf(url):
                continue
            if not _looks_esg(url, title):
                continue

            pdfs.append(url)
            if len(pdfs) >= max_results:
                break

        if pdfs:
            break

    pdfs = list(dict.fromkeys(pdfs))
    print(f"  -> External ESG search found {len(pdfs)} ESG PDFs.")
    return pdfs


def search_esg_html_pages(company_name: str, max_results: int = 5) -> list[str]:
    """
    Use Serper to find ESG-related HTML pages (not PDFs).
    """
    if not SERPER_API_KEY:
        print("  -> SERPER_API_KEY not set; skipping external ESG HTML search.")
        return []

    urls: list[str] = []

    for template in HTML_QUERY_TEMPLATES:
        query = template.format(name=company_name)
        print(f"    -> HTML query: {query}")
        results = _serper_search(query)

        for r in results:
            url = r.get("link")
            title = r.get("title")
            if not url:
                continue
            if _is_pdf(url):
                continue
            if not _looks_esg(url, title):
                continue

            urls.append(url)
            if len(urls) >= max_results:
                break

        if urls:
            break

    urls = list(dict.fromkeys(urls))
    print(f"  -> External ESG HTML search found {len(urls)} pages.")
    return urls


def search_esg_snippets(company_name: str, max_results: int = 15) -> list[str]:
    """
    Use Serper to directly retrieve ESG-related text snippets from the web
    (search result snippets / text fields).

    IMPORTANT:
    - We intentionally pull snippets from ALL query templates (E, S, G).
    - We limit how many snippets we take per query so that we keep
      a balanced mix across Environment, Social, and Governance.
    """
    if not SERPER_API_KEY:
        print("  -> SERPER_API_KEY not set; skipping external ESG snippet search.")
        return []

    snippets: list[str] = []

    # Spread budget roughly evenly per query
    num_queries = len(SNIPPET_QUERY_TEMPLATES)
    per_query_limit = max(2, max_results // num_queries)  # at least 2 each

    for template in SNIPPET_QUERY_TEMPLATES:
        if len(snippets) >= max_results:
            break

        query = template.format(name=company_name)
        print(f"    -> Snippet query: {query}")
        results = _serper_search(query)

        taken_here = 0
        for r in results:
            if len(snippets) >= max_results or taken_here >= per_query_limit:
                break

            snippet = (
                r.get("snippet")
                or r.get("text")
                or r.get("description")
                or ""
            )
            title = r.get("title") or ""
            link = r.get("link") or ""

            combined = "\n".join(
                part for part in [title.strip(), snippet.strip(), link.strip()] if part
            )

            if not combined:
                continue

            snippets.append(combined)
            taken_here += 1

    print(f"  -> External ESG snippet search collected {len(snippets)} text snippets.")
    return snippets