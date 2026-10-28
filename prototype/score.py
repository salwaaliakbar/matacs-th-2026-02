"""Rule checks, weighted scoring and ranking. No AI in this file.

Reads the admin's criteria (criteria.json) and the facts the AI extracted
(extracted.json), and writes ranking.json. Same inputs -> same output, every time.

    python prototype/score.py
"""
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).parent


def round1(x):
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def money(x):
    return f"${x:,}"


def score_one(c, p, eligible):
    """Points (0..weight) for one weighted criterion, plus any flags for a reviewer."""
    w, method = c["weight"], c["method"]

    if method == "count_up_to":
        return w * min(p[c["field"]] / c["full_marks_at"], 1), []

    if method == "lowest_wins":
        value = p[c["field"]]
        if value is None:
            return 0, [f"no committed {c['name']} ({p.get('notes', {}).get(c['field'], 'not stated')})"]
        if value > c["limit"]:
            return 0, [f"{c['name']} {value} is over the limit of {c['limit']}"]
        best = min(q[c["field"]] for q in eligible if q[c["field"]] is not None)
        return w * best / value, []

    if method == "highest_wins":
        parts = [p[f] / max(q[f] for q in eligible) for f in c["fields"]]
        return w * sum(parts) / len(parts), []

    if method == "checklist":
        return w * sum(bool(p[f]) for f in c["fields"]) / len(c["fields"]), []

    raise ValueError(f"unknown method {method}")


def experience_flag(c, p, year):
    """The AI copies the period as written; code decides if it fits the window."""
    since, last_n = p["installs_since_year"], p["installs_in_last_years"]
    if since is not None and since < year - c["window_years"]:
        return [f"installs counted since {since}, beyond the {c['window_years']}-year window"]
    if last_n is not None and last_n > c["window_years"]:
        return [f"installs counted over {last_n} years, beyond the {c['window_years']}-year window"]
    if since is None and last_n is None:
        return ["experience period not stated"]
    return []


def main():
    criteria = json.loads((HERE / "criteria.json").read_text(encoding="utf-8"))
    proposals = json.loads((HERE / "extracted.json").read_text(encoding="utf-8"))
    proposals = {k: v for k, v in proposals.items() if not k.startswith("_")}

    # 1. Mandatory gates (pass/fail)
    failed = {}
    for pid, p in proposals.items():
        for gate in criteria["mandatory"]:
            if not all(p[f] is True for f in gate["fields"]):
                note = next((p.get("notes", {})[f] for f in gate["fields"] if f in p.get("notes", {})), "not stated")
                failed[pid] = f"{gate['label']} ({note})"
                break
    eligible = {pid: p for pid, p in proposals.items() if pid not in failed}

    # 2. Weighted scoring + flags for anything a person must look at
    results = {}
    for pid, p in eligible.items():
        flags = ["hidden text tells automated reviewers to rank it first (ignored in scoring)"] if p["embedded_instructions"] else []
        points = {}
        for c in criteria["weighted"]:
            pts, f = score_one(c, p, list(eligible.values()))
            if c["name"] == "experience":
                f += experience_flag(c, p, criteria["scoring_year"])
            points[c["name"]] = round(pts, 2)
            flags += f
        results[pid] = {"score": round1(sum(points.values())), "points": points, "flags": flags}

    # 3. Rank only proposals with no open flags
    clean = sorted((pid for pid in results if not results[pid]["flags"]), key=lambda pid: -results[pid]["score"])

    out = []
    for rank, pid in enumerate(clean, 1):
        out.append({"proposal": pid, "rank": rank, "status": "ranked", "score": results[pid]["score"],
                    "reason": ranked_reason(criteria, proposals[pid], results[pid]["points"])})
    for pid in sorted(results):
        if results[pid]["flags"]:
            s = results[pid]["score"]
            out.append({"proposal": pid, "rank": None, "status": "flagged", "score": s,
                        "reason": "Held for reviewer: " + "; ".join(results[pid]["flags"])
                                  + f". Provisional score {s}, not ranked until resolved."})
    for pid in sorted(failed):
        out.append({"proposal": pid, "rank": None, "status": "ineligible", "score": None,
                    "reason": f"Fails mandatory check: {failed[pid]}. Not scored."})

    text = "[\n" + ",\n".join("  " + json.dumps(o, ensure_ascii=False) for o in out) + "\n]\n"
    (HERE.parent / "ranking.json").write_text(text, encoding="utf-8")
    print(text)
    for pid, r in sorted(results.items()):
        print(pid, r["score"], r["points"])


def ranked_reason(criteria, p, points):
    team = next(c for c in criteria["weighted"] if c["name"] == "team")
    shown = {
        "experience": f"{p['installs_100kw_plus']} installs",
        "price": money(p["total_price_cad"]),
        "timeline": f"{p['completion_weeks']} weeks",
        "warranty": f"{p['panel_warranty_years']}-yr panel, {p['workmanship_warranty_years']}-yr workmanship",
        "team": f"{sum(bool(p[f]) for f in team['fields'])} of {len(team['fields'])} team items",
    }
    weights = {c["name"]: c["weight"] for c in criteria["weighted"]}
    full = [n for n in points if weights[n] - points[n] < 0.05]
    lost = [f"{n} ({shown[n]}, {round1(points[n]):g}/{weights[n]})" for n in points if n not in full]
    return f"Passes both mandatory checks. Full marks: {', '.join(full)}. Lost points: {', '.join(lost)}."


if __name__ == "__main__":
    main()
