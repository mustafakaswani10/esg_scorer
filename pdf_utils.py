# pdf_utils.py

from typing import List
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

import requests
from pypdf import PdfReader


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ESGScraper/1.0)"
}


def _extract_single_pdf(url: str, timeout: int = 40) -> str:
    """
    Download a single PDF and extract text.
    Returns empty string on any failure.
    """
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()

        data = BytesIO(resp.content)
        reader = PdfReader(data)

        pages_text = []
        for page in reader.pages:
            try:
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(text)
            except Exception:
                continue

        return "\n".join(pages_text)
    except Exception:
        return ""


def extract_pdf_texts(urls: List[str], max_workers: int = 5) -> List[str]:
    """
    Download and extract text from a list of PDF URLs in parallel.

    Returns:
        List of text contents in the SAME order as the input URLs.
        If a PDF fails, the corresponding entry is an empty string.
    """
    if not urls:
        return []

    results: List[str] = [""] * len(urls)
    indexed_urls = list(enumerate(urls))

    def worker(idx_and_url):
        idx, url = idx_and_url
        text = _extract_single_pdf(url)
        return idx, text

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for idx, text in ex.map(worker, indexed_urls):
            results[idx] = text

    return results