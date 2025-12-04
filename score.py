# score.py

from typing import Dict, Any


def _clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))


def _score_environment(E: Dict[str, Any]) -> int:
    score = 0.0

    # Core climate posture
    if E.get("has_net_zero_target"):
        score += 35
        year = E.get("net_zero_year")
        if isinstance(year, int):
            if year <= 2030:
                score += 5
            elif year <= 2050:
                score += 2

    if E.get("uses_renewable_energy"):
        score += 25
        pct = E.get("renewable_share_pct")
        if isinstance(pct, (int, float)):
            # small bonus if we know the share
            score += min(pct * 0.1, 5)  # up to +5

    # Disclosure is now a bonus, not the backbone of E
    if E.get("discloses_scope_1_2"):
        score += 10
    if E.get("discloses_scope_3"):
        score += 10

    return int(round(_clamp(score)))


def _score_social(S: Dict[str, Any]) -> int:
    score = 0.0

    # Core "hard" social signals
    if S.get("has_diversity_policy"):
        score += 20
        pct = S.get("female_leadership_pct")
        if isinstance(pct, (int, float)):
            if pct >= 40:
                score += 15
            elif pct >= 25:
                score += 10
            elif pct >= 10:
                score += 5

    if S.get("employee_wellbeing_programs"):
        score += 15
    if S.get("workplace_safety_programs"):
        score += 15
    if S.get("community_programs"):
        score += 15

    # Softer "mentions" signals – partial credit like we effectively did for E
    if S.get("mentions_diversity_or_inclusion"):
        score += 10
    if S.get("mentions_employee_safety_or_health"):
        score += 10
    if S.get("mentions_community_or_philanthropy"):
        score += 10

    return int(round(_clamp(score)))


def _score_governance(G: Dict[str, Any]) -> int:
    score = 0.0

    # Core "hard" governance signals
    if G.get("has_independent_board"):
        score += 20
        pct = G.get("board_independence_pct")
        if isinstance(pct, (int, float)):
            if pct >= 60:
                score += 15
            elif pct >= 40:
                score += 10
            elif pct >= 25:
                score += 5

    if G.get("has_anti_corruption_policy"):
        score += 15
    if G.get("has_whistleblower_mechanism"):
        score += 15
    if G.get("has_esg_governance_structure"):
        score += 20

    # Softer "mentions" signals – partial credit
    if G.get("mentions_board_or_directors"):
        score += 10
    if G.get("mentions_ethics_or_code_of_conduct"):
        score += 10
    if G.get("mentions_compliance_or_risk_management"):
        score += 10

    return int(round(_clamp(score)))


def compute_esg_scores(esg_signals: Dict[str, Any]) -> Dict[str, int]:
    E_signals = esg_signals.get("E", {}) or {}
    S_signals = esg_signals.get("S", {}) or {}
    G_signals = esg_signals.get("G", {}) or {}

    e = _score_environment(E_signals)
    s = _score_social(S_signals)
    g = _score_governance(G_signals)

    total = int(round((e + s + g) / 3)) if (e or s or g) else 0

    return {"E": e, "S": s, "G": g, "total": total}