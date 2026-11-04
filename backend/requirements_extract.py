"""Consultant Agent: turns a transcript into a structured requirement document."""
import re

def extract(text: str, prev: dict | None = None) -> dict:
    t = text.lower().replace("×", "x").replace("*", "x")
    r = dict(prev or {})
    if m := re.search(r"(\d+)\s*(?:x|by)\s*(\d+)", t):
        r["plot_w"], r["plot_d"] = int(m[1]), int(m[2])
    if m := re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|crore|crores|cr)\b", t):
        r["budget"] = int(float(m[1]) * (1e7 if m[2].startswith("cr") else 1e5))
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    if m := re.search(r"(\d|one|two|three|four|five)\s*(?:bhk|bed)", t):
        r["bedrooms"] = int(m[1]) if m[1].isdigit() else words[m[1]]
    if "duplex" in t or "two floor" in t or "g+1" in t: r["floors"] = 2
    elif "single floor" in t or "ground floor" in t: r["floors"] = 1
    r.setdefault("floors", 1)
    if m := re.search(r"\bin ([a-z]+(?: [a-z]+)??)(?: with| and|,|\.|$)", t): r["city"] = m[1].strip().title()
    for k, pat in {"study": r"study|home office|office", "garden": r"garden|lawn",
                   "solar": r"solar", "open_kitchen": r"open kitchen", "modern": r"modern"}.items():
        if re.search(pat, t): r[k] = True
    if m := re.search(r"(one|two|three|\d)[- ]car", t):
        r["parking"] = words.get(m[1]) or int(m[1])
    elif "parking" in t: r["parking"] = r.get("parking", 1)
    asked_vastu = prev is not None and "vastu" not in prev
    if re.search(r"no vastu|without vastu|don'?t need vastu", t): r["vastu"] = False
    elif "vastu" in t: r["vastu"] = True
    elif asked_vastu and re.search(r"\b(yes|yeah|sure|please)\b", t): r["vastu"] = True
    elif asked_vastu and re.search(r"\bno\b", t): r["vastu"] = False
    r.setdefault("city", "Hyderabad"); r.setdefault("bedrooms", 3)
    return r

def follow_up(r: dict) -> str | None:
    if "plot_w" not in r: return "What are your plot dimensions, for example 30 by 40 feet?"
    if "budget" not in r: return "What is your total budget for construction?"
    if "vastu" not in r: return "Would you like Vastu compliance?"
    return None
