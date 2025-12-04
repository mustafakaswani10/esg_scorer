# explain.py
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are an ESG consultant. Explain ESG scores in concise, business-friendly language."
)


def explain_scores(root_url: str, esg_signals: dict, esg_scores: dict) -> str:
    payload = {
        "url": root_url,
        "scores": esg_scores,
        "signals": esg_signals,
    }

    prompt = (
        "Using the JSON data below, write:\n"
        "1) A 120-word overview of the company's ESG performance.\n"
        "2) Three key strengths (bullet points).\n"
        "3) Three priority improvement actions (bullet points).\n\n"
        f"Data:\n{json.dumps(payload, indent=2)}"
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()