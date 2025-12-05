# text_utils.py

from typing import Iterable, List


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    """Return a list with duplicates removed while keeping original order."""

    seen = set()
    unique: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique

def combine_pages_text(pages: dict) -> str:
    """
    Join a dict of {url: cleaned_text} into one large text block.
    """
    parts = []
    for url, txt in pages.items():
        if txt.strip():
            parts.append(f"[URL: {url}]\n{txt.strip()}\n")
    return "\n\n".join(parts)


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    Default: 2000 char chunks with 200 char overlap.
    """
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])

        if end == length:
            break

        # Move forward by (chunk_size - overlap)
        start = end - overlap

    return chunks