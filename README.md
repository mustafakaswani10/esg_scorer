ESG Score Generator (Web Scraper + GenAI + PDF Analyzer)

This project builds an end-to-end ESG (Environmental, Social, Governance) scoring pipeline using:
	•	Web scraping
	•	PDF extraction
	•	Vector embeddings
	•	LLM-based ESG signal extraction
	•	Rule-based scoring
	•	Generative narrative summary

It takes either a company name OR a URL, automatically discovers ESG sources (webpages + PDFs), analyzes them, and returns:
	•	ESG scores (E, S, G, Total)
	•	Extracted ESG evidence
	•	A generated ESG performance explanation

This is a fully automated ESG intelligence engine using real corporate data.

⸻

Features

1. Automatic Company Discovery

Input can be either:
	•	netflix
	•	microsoft
	•	apple.com
	•	https://about.netflix.com/sustainability

The system:
	1.	Detects the likely domain
	2.	Crawls the website for ESG content
	3.	Scrapes ESG-related HTML pages and links
	4.	Detects on-site ESG PDFs (CSR reports, sustainability reports, impact reports)

⸻

2. External ESG PDF Search (Serper.dev + Google Results)

If input is a company name, the system also queries Google via Serper.dev:
	•	"Netflix ESG report pdf"
	•	"Netflix sustainability report pdf"

It retrieves actual ESG reports from the wider web, not just the company’s homepage.

This dramatically improves coverage and accuracy.

⸻

3. PDF Extraction

All discovered PDFs are downloaded and parsed using pypdf:
	•	Sustainability/ESG reports
	•	CSR documents
	•	Annual governance reports

Their text is merged with HTML content from the crawl.

⸻

4. Embedding + LLM Analysis

The system:
	•	Chunks all extracted text
	•	Generates embeddings with Sentence Transformers
	•	Uses an LLM to extract structured ESG signals:
	•	Net-zero commitments
	•	Emissions disclosures
	•	Diversity statistics
	•	Anti-corruption policies
	•	Governance structures
	•	Community initiatives
	•	Environmental actions

⸻

5. ESG Scoring Engine

A rule-based system converts extracted signals into numeric ESG scores:
	•	E: 0–100
	•	S: 0–100
	•	G: 0–100
	•	Total: weighted aggregate

⸻

6. Narrative ESG Summary

The LLM produces:
	•	A human-readable overview
	•	Key strengths
	•	Priority improvement actions
	•	Rating explanation

⸻

Project Structure

esg_scorer/
│
├── main.py                 # Entry point (interactive)
├── scrape.py               # Site crawler (HTML + ESG PDFs on site)
├── esg_search.py           # External ESG PDF search using Serper.dev
├── pdf_utils.py            # PDF download + parsing
├── text_utils.py           # Chunking, text processing
├── esg_extract.py          # LLM ESG signal extraction per chunk
├── score.py                # Rule-based ESG scoring
├── explain.py              # LLM narrative generation
├── domain_lookup.py        # Simple domain guesser
├── requirements.txt
└── README.md

Installation

1. Clone project and create virtual environment

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Export API keys

You need:
	•	OpenAI API key
	•	Serper.dev API key

export OPENAI_API_KEY="sk-..."
export SERPER_API_KEY="serper-..."

Usage

Run:
python main.py
Example Input:
Enter a company name or URL: netflix

Pipeline:
	•	Crawls https://netflix.com
	•	Discovers no on-site ESG PDFs
	•	Uses Serper to find ESG PDFs externally
	•	Finds:
	•	Netflix_2022-ESG-Report-FINAL.pdf
	•	NASDAQ_NFLX_2020 Responsibility Report.pdf
	•	Downloads + extracts both
	•	Embeds + chunks
	•	Runs ESG extraction
	•	Computes ESG scores
	•	Generates narrative

Output (summarized)

Done. Scores:
{'E': 50, 'S': 80, 'G': 55, 'total': 60}

External ESG PDFs:
 - https://downloads.ctfassets.net/...Netflix_2022-ESG-Report-FINAL.pdf
 - https://www.responsibilityreports.com/...NASDAQ_NFLX_2020.pdf

 LLM Narrative Summary (excerpt):

Netflix demonstrates a solid ESG performance with a total score of 60, reflecting balanced efforts across environmental, social, and governance dimensions.
Achieved its net-zero 2022 commitment…
Strong diversity policies, workplace safety, community involvement…
Independent board and anti-corruption policies…
Recommended improvements include increasing renewable energy share, strengthening governance best practices, and addressing ecosystem risks.

Why This Project Matters

It demonstrates real applied ML/AI engineering, including:
	•	Multistage data ingestion
	•	Robust web scraping
	•	PDF data extraction
	•	Information retrieval
	•	Embedding-driven analysis
	•	LLM orchestration
	•	Rule-based scoring
	•	Real-world ESG domain modeling

Perfect to showcase:
	•	AI engineering
	•	Data science
	•	NLP/RAG
	•	Real-world automation
	•	ML systems design

⸻

Future Extensions (Optional)
	•	Multi-query ESG PDF search for higher recall
	•	Caching of crawled pages + PDFs
	•	Use Azure/Bing search instead of Serper
	•	Graph-based ESG signal weighting
	•	Multi-year ESG trend analysis
	•	Dashboard for scores
	•	Batch mode for entire portfolios

⸻

License

Open-source for learning, academic, and portfolio purposes.

