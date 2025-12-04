# esg_extract.py

from typing import List, Dict, Any
from openai import OpenAI
import json

client = OpenAI()

# Use a stronger model for ESG extraction
ESG_MODEL = "gpt-4o"  # change to gpt-4o-mini if you want it cheaper


def _build_prompt(text: str) -> str:
    return f"""
You are an ESG analyst. You will be given text from ESG, sustainability, or impact reports
and related analysis about a single company.

Your job is to extract clear, factual ESG signals and output a STRICT JSON object
with this exact structure and keys:

{{
  "E": {{
    "has_net_zero_target": true/false,
    "net_zero_year": int or null,
    "uses_renewable_energy": true/false,
    "renewable_share_pct": float or null,
    "discloses_scope_1_2": true/false,
    "discloses_scope_3": true/false
  }},
  "S": {{
    "has_diversity_policy": true/false,
    "female_leadership_pct": float or null,
    "employee_wellbeing_programs": true/false,
    "workplace_safety_programs": true/false,
    "community_programs": true/false,

    "mentions_diversity_or_inclusion": true/false,
    "mentions_employee_safety_or_health": true/false,
    "mentions_community_or_philanthropy": true/false
  }},
  "G": {{
    "has_independent_board": true/false,
    "board_independence_pct": float or null,
    "has_anti_corruption_policy": true/false,
    "has_whistleblower_mechanism": true/false,
    "has_esg_governance_structure": true/false,

    "mentions_board_or_directors": true/false,
    "mentions_ethics_or_code_of_conduct": true/false,
    "mentions_compliance_or_risk_management": true/false
  }}
}}

INTERPRETATION RULES (VERY IMPORTANT):

ENVIRONMENT (E)
- If the text clearly indicates a climate or net-zero target, set has_net_zero_target=true.
  Examples:
  - "We target net-zero by 2030" -> has_net_zero_target=true, net_zero_year=2030
  - "Net-zero emissions by 2050" -> has_net_zero_target=true, net_zero_year=2050
- If the company mentions specific years but not the phrase "net-zero", still use them
  if the context is clearly about emissions neutrality.
- If the company uses renewable or clean energy in a material way, set uses_renewable_energy=true.
- If a percentage of energy from renewables is given, set renewable_share_pct to that value.
- If greenhouse gas emissions for Scope 1 and 2 are disclosed, set discloses_scope_1_2=true.
- If Scope 3 emissions are disclosed, set discloses_scope_3=true.
- If the text does not mention something at all, set the boolean to false and numeric fields to null.

SOCIAL (S)
- has_diversity_policy:
  - Set to true if there is any indication of a formal or informal diversity, equity,
    or inclusion policy, program, or commitment.
  - Phrases like "diversity & inclusion", "DEI", "equal opportunities" count.
- female_leadership_pct:
  - If a percentage of women in leadership, management, or the board is given, use that.
  - If described qualitatively (e.g. "about one third of leaders are women"), approximate:
    - "about one third" -> ≈33.0
    - "around half" -> ≈50.0
  - If not clear or not mentioned, set to null.
- employee_wellbeing_programs:
  - True if the text discusses structured wellbeing programs, mental health support,
    benefits focused on wellbeing, etc.
- workplace_safety_programs:
  - True if there are policies or programs specifically for workplace safety, incident prevention,
    or occupational health and safety management systems.
- community_programs:
  - True if the company is running community engagement, philanthropy, social impact, or similar programs.

- mentions_diversity_or_inclusion:
  - True if the text mentions diversity, inclusion, equity, equal opportunity, DEI, etc at all,
    even without describing a full policy.
- mentions_employee_safety_or_health:
  - True if the text mentions worker safety, occupational health, injury reduction, health & safety,
    or similar topics at all.
- mentions_community_or_philanthropy:
  - True if the text mentions communities, charitable activities, philanthropy, donations,
    volunteering, or community impact.

GOVERNANCE (G)
- has_independent_board:
  - True if there is explicit mention of independent directors or an independent board structure.
- board_independence_pct:
  - If a percentage of independent directors is given, set this value.
  - If described qualitatively ("around one third of our board is independent"), approximate.
- has_anti_corruption_policy:
  - True if there is mention of an anti-corruption policy, anti-bribery policy, ethics policy
    that includes anti-corruption themes.
- has_whistleblower_mechanism:
  - True if the text refers to a whistleblower process, hotline, reporting mechanism, speak-up line,
    or equivalent.
- has_esg_governance_structure:
  - True if there is mention of an ESG committee, sustainability committee, board-level oversight
    of ESG or sustainability, or dedicated ESG governance structures.

- mentions_board_or_directors:
  - True if there is any discussion of the board of directors, board committees, or board oversight.
- mentions_ethics_or_code_of_conduct:
  - True if the text mentions ethics, ethical behavior, conduct, code of conduct, integrity.
- mentions_compliance_or_risk_management:
  - True if the text mentions compliance, regulatory compliance, risk management frameworks,
    internal controls, or similar topics.

GENERAL RULES
- If the text clearly indicates a positive signal, set the boolean to true.
- If the text clearly contradicts a signal, set it to false.
- If the text does not mention a topic at all, set the boolean to false and numeric fields to null.
- For percentages, use best approximate values when text is clear; otherwise leave as null.

Return ONLY the JSON object, no explanation, no markdown, no extra keys.

Here is the text to analyze (may be long):

\"\"\" 
{text}
\"\"\" 
"""


def _default_structure() -> Dict[str, Any]:
    return {
        "E": {
            "has_net_zero_target": False,
            "net_zero_year": None,
            "uses_renewable_energy": False,
            "renewable_share_pct": None,
            "discloses_scope_1_2": False,
            "discloses_scope_3": False,
        },
        "S": {
            "has_diversity_policy": False,
            "female_leadership_pct": None,
            "employee_wellbeing_programs": False,
            "workplace_safety_programs": False,
            "community_programs": False,

            "mentions_diversity_or_inclusion": False,
            "mentions_employee_safety_or_health": False,
            "mentions_community_or_philanthropy": False,
        },
        "G": {
            "has_independent_board": False,
            "board_independence_pct": None,
            "has_anti_corruption_policy": False,
            "has_whistleblower_mechanism": False,
            "has_esg_governance_structure": False,

            "mentions_board_or_directors": False,
            "mentions_ethics_or_code_of_conduct": False,
            "mentions_compliance_or_risk_management": False,
        },
    }


def _ensure_structure(d: Dict[str, Any]) -> Dict[str, Any]:
    base = _default_structure()
    for pillar in base:
        if pillar not in d or not isinstance(d[pillar], dict):
            d[pillar] = {}
        for k, v in base[pillar].items():
            d[pillar].setdefault(k, v)
    return d


def _call_llm_for_esg(text: str) -> Dict[str, Any]:
    prompt = _build_prompt(text)

    resp = client.chat.completions.create(
        model=ESG_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a precise ESG analyst. Always output valid JSON that matches the requested schema.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    raw = resp.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except Exception:
        data = _default_structure()

    data = _ensure_structure(data)
    return data


def extract_esg_signals(chunks: List[str]) -> Dict[str, Any]:
    """
    Takes a list of text chunks and returns a single ESG signal dict.
    We join up to ~50k characters so the model sees enough context
    without hitting context limits.
    """
    if not chunks:
        return _default_structure()

    max_chars = 50000
    combined = ""
    for ch in chunks:
        if len(combined) + len(ch) > max_chars:
            break
        combined += "\n\n" + ch

    return _call_llm_for_esg(combined)