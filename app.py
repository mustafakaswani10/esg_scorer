# app.py
import textwrap
from typing import Optional

import streamlit as st

from main import score_website, normalize_input


def infer_company_hint(raw: str) -> Optional[str]:
    """
    Mirror the logic in main.py:
    If the input looks like a URL or has a dot, we don't treat it as a plain company name.
    Otherwise, we pass it as company_name for ESG web search.
    """
    raw = raw.strip()
    if not raw:
        return None

    if raw.startswith("http://") or raw.startswith("https://") or "." in raw:
        return None
    return raw


def main():
    st.set_page_config(
        page_title="ESG Scorer",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 ESG Scorer")
    st.markdown(
        "Enter a **company name** (e.g. `tesla`, `adidas`) or a **URL** "
        "(e.g. `https://www.microsoft.com/en-us/corporate-responsibility/sustainability`)."
    )

    with st.sidebar:
        st.header("Settings")
        st.markdown(
            "- Uses web crawling + ESG PDFs + ESG snippets\n"
            "- Extracts ESG signals with an LLM\n"
            "- Computes E/S/G scores out of 100"
        )

    default_example = "tesla"
    raw_input_value = st.text_input(
        "Company name or URL",
        value=default_example,
        help="You can type a bare company name (e.g. `adidas`) or a full URL.",
    )

    run_button = st.button("Run ESG analysis", type="primary")

    if not run_button:
        st.stop()

    if not raw_input_value.strip():
        st.error("Please enter a company name or URL.")
        st.stop()

    with st.spinner("Running ESG analysis. This may take a bit for large reports..."):
        company_hint = infer_company_hint(raw_input_value)
        url = normalize_input(raw_input_value)

        result = score_website(url, company_name=company_hint)

    # === Scores section ===
    st.subheader("ESG Scores")

    scores = result.get("esg_scores", {})
    col_e, col_s, col_g, col_total = st.columns(4)

    with col_e:
        st.metric("Environmental (E)", scores.get("E", 0))
    with col_s:
        st.metric("Social (S)", scores.get("S", 0))
    with col_g:
        st.metric("Governance (G)", scores.get("G", 0))
    with col_total:
        st.metric("Total ESG score", scores.get("total", 0))

    # === Explanation ===
    st.subheader("Narrative explanation")
    explanation = result.get("explanation", "")
    if explanation:
        st.write(explanation)
    else:
        st.write("No explanation was generated.")

    # === Signals (debug / transparency) ===
    with st.expander("Show extracted ESG signals (debug)"):
        st.json(result.get("esg_signals", {}))

    # === Sources used ===
    st.subheader("Sources used")

    crawled = result.get("crawled_urls", [])
    external_html = result.get("external_html_urls", [])
    on_site_pdfs = result.get("pdf_urls_on_site", [])
    external_pdfs = result.get("external_pdf_urls", [])
    snippets_count = result.get("external_snippets_count", 0)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**On-site HTML pages**")
        if crawled:
            for u in crawled:
                st.write(f"- {u}")
        else:
            st.write("_None_")

        st.markdown("**On-site ESG PDFs**")
        if on_site_pdfs:
            for u in on_site_pdfs:
                st.write(f"- {u}")
        else:
            st.write("_None_")

    with col2:
        st.markdown("**External ESG HTML pages (web search)**")
        if external_html:
            for u in external_html:
                st.write(f"- {u}")
        else:
            st.write("_None_")

        st.markdown("**External ESG PDFs (web search)**")
        if external_pdfs:
            for u in external_pdfs:
                st.write(f"- {u}")
        else:
            st.write("_None_")

        st.markdown(f"**External ESG snippets used:** {snippets_count}")

    # Footer
    st.markdown("---")
    st.caption(
        "Prototype ESG scoring tool. Scores are heuristic and based on public web content; "
        "treat as indicative, not as an official ESG rating."
    )


if __name__ == "__main__":
    main()
