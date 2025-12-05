# main.py
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from scrape import crawl_site, fetch_html, html_to_text
from text_utils import combine_pages_text, chunk_text, dedupe_preserve_order
from esg_extract import extract_esg_signals
from score import compute_esg_scores
from explain import explain_scores
from domain_lookup import lookup_domain
from pdf_utils import extract_pdf_texts
from esg_search import (
    search_esg_pdfs,
    search_esg_html_pages,
    search_esg_snippets,
)


@dataclass
class CrawlResult:
    pages: dict[str, str]
    pdf_urls: list[str]


@dataclass
class ExternalSources:
    pdf_urls: list[str] = field(default_factory=list)
    html_urls: list[str] = field(default_factory=list)
    snippets: list[str] = field(default_factory=list)


def crawl_with_fallback(root_url: str) -> CrawlResult:
    """
    1) First try ESG-only crawl (URLs with sustainability/ESG keywords).
    2) If we get too few pages, fall back to a broader same-domain crawl.
    Returns:
        pages: dict[url -> text]
        pdf_urls_on_site: list[str]
    """
    print("  -> ESG-focused crawl...")
    pages, pdfs = crawl_site(root_url, max_pages=15, max_depth=2, esg_only=True)

    if len(pages) >= 3 or pdfs:
        print(f"  -> ESG-focused crawl found {len(pages)} pages and {len(pdfs)} ESG PDFs.")
        return CrawlResult(pages=pages, pdf_urls=pdfs)

    print(f"  -> Only {len(pages)} ESG pages and {len(pdfs)} ESG PDFs found. Falling back to full-site crawl...")
    pages_full, pdfs_full = crawl_site(root_url, max_pages=10, max_depth=1, esg_only=False)
    print(f"  -> Full-site crawl found {len(pages_full)} pages and {len(pdfs_full)} ESG PDFs.")

    pages_result = pages_full or pages
    pdfs_result = pdfs_full or pdfs
    return CrawlResult(pages=pages_result, pdf_urls=pdfs_result)


def count_esg_evidence(esg_signals: dict) -> int:
    """
    Count how many 'meaningful' ESG data points we have.
    Rough heuristic to decide if we have enough for a narrative explanation.
    """
    count = 0
    for pillar in esg_signals.values():
        for v in pillar.values():
            if isinstance(v, bool) and v:
                count += 1
            elif isinstance(v, (int, float)) and v not in (0, None):
                count += 1
            elif isinstance(v, str) and v.strip():
                count += 1
            elif isinstance(v, list) and len(v) > 0:
                count += 1
    return count


def search_external_sources(company_name: str) -> ExternalSources:
    print(f"  -> Searching external web for ESG PDFs for '{company_name}'...")
    external_pdf_urls = search_esg_pdfs(company_name)

    print(f"  -> Searching external web for ESG HTML pages for '{company_name}'...")
    external_html_urls = search_esg_html_pages(company_name)

    print(f"  -> Searching external web for ESG text snippets for '{company_name}'...")
    external_snippets = search_esg_snippets(company_name)

    return ExternalSources(
        pdf_urls=external_pdf_urls,
        html_urls=external_html_urls,
        snippets=external_snippets,
    )


def fetch_external_html_texts(urls: list[str]) -> list[str]:
    def fetch_and_clean(url: str) -> str:
        try:
            html = fetch_html(url)
            txt = html_to_text(html)
            return txt.strip()
        except Exception:
            return ""

    external_html_pages_text: list[str] = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        for txt in ex.map(fetch_and_clean, urls):
            if txt:
                external_html_pages_text.append(txt)
    return external_html_pages_text


def combine_text_sources(
    pdf_texts: list[str],
    external_html_texts: list[str],
    serper_snippets: list[str],
    on_site_text: str,
) -> str:
    combined_parts: list[str] = []

    if pdf_texts:
        combined_parts.append("\n\n".join(pdf_texts))
    if external_html_texts:
        combined_parts.append("\n\n".join(external_html_texts))
    if serper_snippets:
        combined_parts.append("\n\n".join(serper_snippets))
    if on_site_text:
        combined_parts.append(on_site_text)

    return "\n\n".join(combined_parts).strip()


def build_empty_text_response(
    root_url: str,
    crawl_result: CrawlResult,
    external_sources: ExternalSources,
) -> dict:
    esg_scores = {"E": 0, "S": 0, "G": 0, "total": 0}
    explanation = (
        "The system could not extract any machine-readable ESG-related text from the website, "
        "external reports, or search snippets. This may happen if reports are image-only scans "
        "or behind complex rendering. Treat this as 'no rating', not as evidence of weak ESG."
    )

    return {
        "root_url": root_url,
        "crawled_urls": list(crawl_result.pages.keys()),
        "pdf_urls_on_site": crawl_result.pdf_urls,
        "external_pdf_urls": external_sources.pdf_urls,
        "external_html_urls": external_sources.html_urls,
        "external_snippets_count": len(external_sources.snippets),
        "esg_signals": {},
        "esg_scores": esg_scores,
        "explanation": explanation,
    }


def score_website(root_url: str, company_name: Optional[str] = None) -> dict:
    # 1) On-site crawl
    crawl_result = crawl_with_fallback(root_url)

    # 2) External ESG search (PDFs + HTML + snippets)
    external_sources = search_external_sources(company_name) if company_name else ExternalSources()

    # 3) Merge PDF URLs (on-site + external, de-duplicated)
    all_pdf_urls = dedupe_preserve_order(crawl_result.pdf_urls + external_sources.pdf_urls)

    # 4) On-site HTML text
    print("  -> Combining on-site HTML text...")
    on_site_text = combine_pages_text(crawl_result.pages) if crawl_result.pages else ""
    print("  -> Combined on-site HTML text length:", len(on_site_text))

    # 5) External ESG HTML text (PARALLEL FETCH)
    external_html_pages_text: list[str] = []
    if external_sources.html_urls:
        print(
            f"  -> Downloading and extracting {len(external_sources.html_urls)} external ESG HTML pages in parallel..."
        )
        external_html_pages_text = fetch_external_html_texts(external_sources.html_urls)

    print("  -> Combined external ESG HTML text length:", len("\n\n".join(external_html_pages_text)))

    # 6) PDF text (PARALLEL DOWNLOAD + EXTRACT inside extract_pdf_texts)
    print(f"  -> Downloading and extracting {len(all_pdf_urls)} ESG PDFs in parallel...")
    pdf_texts = extract_pdf_texts(all_pdf_urls, max_workers=5)
    combined_pdf_text = "\n\n".join(pdf_texts) if pdf_texts else ""
    print("  -> Combined PDF text length:", len(combined_pdf_text))

    # 7) Serper ESG snippets text
    serper_snippets_text = external_sources.snippets
    print("  -> Combined Serper snippet text length:", len("\n\n".join(serper_snippets_text)))

    # 8) Combine everything with ESG priority:
    #    PDFs -> external ESG HTML -> snippets -> on-site HTML
    combined_text = combine_text_sources(
        pdf_texts=pdf_texts,
        external_html_texts=external_html_pages_text,
        serper_snippets=serper_snippets_text,
        on_site_text=on_site_text,
    )

    print("  -> Combined TOTAL text length:", len(combined_text))

    if not combined_text:
        print("  -> No extractable text found in HTML, PDFs, or snippets. Returning 'no rating' result.")
        return build_empty_text_response(root_url, crawl_result, external_sources)

    # 9) Chunk + extract
    print("  -> Chunking combined text...")
    chunks = chunk_text(combined_text, chunk_size=2000, overlap=200)

    print("  -> Extracting ESG signals with LLM...")
    esg_signals = extract_esg_signals(chunks)
    print("  -> ESG signals extracted:")
    print(esg_signals)

    print("  -> Computing ESG scores...")
    esg_scores = compute_esg_scores(esg_signals)

    evidence = count_esg_evidence(esg_signals)
    print(f"  -> ESG evidence points found: {evidence}")

    if evidence < 3:
        explanation = (
            "The system found only limited ESG-related content across the website and external sources. "
            "The scores here should be treated as 'no rating' or very low-confidence, rather than a "
            "definitive assessment of ESG performance."
        )
    else:
        print("  -> Generating explanation...")
        explanation = explain_scores(root_url, esg_signals, esg_scores)

    return {
        "root_url": root_url,
        "crawled_urls": list(crawl_result.pages.keys()),
        "pdf_urls_on_site": crawl_result.pdf_urls,
        "external_pdf_urls": external_sources.pdf_urls,
        "external_html_urls": external_sources.html_urls,
        "external_snippets_count": len(external_sources.snippets),
        "esg_signals": esg_signals,
        "esg_scores": esg_scores,
        "explanation": explanation,
    }


def normalize_input(user_input: str) -> str:
    """
    If user enters:
        - full URL -> return as-is
        - domain -> prepend https://
        - company name -> try web search to find official domain
    """
    user_input = user_input.strip()

    if user_input.startswith("http://") or user_input.startswith("https://"):
        return user_input

    if "." in user_input:
        return f"https://{user_input}"

    print(f"Looking up official domain for company name: '{user_input}'...")
    guess = lookup_domain(user_input)
    if guess:
        print(f"  -> Detected official site: {guess}")
        return guess

    print("  -> Could not detect domain via search, falling back to https://<name>.com")
    return f"https://{user_input}.com"


if __name__ == "__main__":
    raw = input("Enter a company name or URL (e.g. 'microsoft' or 'https://www.apple.com'): ").strip()

    if not raw:
        raw = "https://www.microsoft.com/en-us/corporate-responsibility/sustainability"

    if raw.startswith("http://") or raw.startswith("https://") or "." in raw:
        company_hint: Optional[str] = None
    else:
        company_hint = raw

    url = normalize_input(raw)

    print(f"\nStarting ESG scoring for: {url}")
    result = score_website(url, company_name=company_hint)

    print("\nDone. Scores:")
    print(result["esg_scores"])

    print("\nHTML pages used (on-site):")
    for u in result["crawled_urls"]:
        print(" -", u)

    if result.get("external_html_urls"):
        print("\nExternal ESG HTML pages (from web search):")
        for u in result["external_html_urls"]:
            print(" -", u)

    if result["pdf_urls_on_site"]:
        print("\nOn-site ESG PDFs:")
        for u in result["pdf_urls_on_site"]:
            print(" -", u)

    if result["external_pdf_urls"]:
        print("\nExternal ESG PDFs (from web search):")
        for u in result["external_pdf_urls"]:
            print(" -", u)

    print(f"\nExternal ESG snippets used: {result.get('external_snippets_count', 0)}")

    print("\nExplanation:\n")
    print(result["explanation"])
    print()