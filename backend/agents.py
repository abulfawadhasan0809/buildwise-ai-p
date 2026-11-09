"""Cost, sustainability, timeline, interior, utility and explanation agents."""
import os

def built_area(r):
    return int(r.get("plot_w", 30) * r.get("plot_d", 40) * 0.65 * r.get("floors", 1))

CITY = {"hyderabad": 1.0, "bengaluru": 1.12, "bangalore": 1.12, "mumbai": 1.6, "delhi": 1.2, "chennai": 1.05, "pune": 1.1,
        "kolkata": .95, "ahmedabad": .95, "jaipur": .9, "vijayawada": .9, "visakhapatnam": .92}
TIER = {"basic": (1500, 550), "standard": (1850, 800), "premium": (2600, 1400)}  # INR/sqft: construction, interiors

def cost(r, _sug=True):
    a = built_area(r); tier = r.get("quality") or "standard"
    cf = CITY.get(str(r.get("city", "")).lower(), 1.0); base_rate, int_rate = TIER[tier]
    base = a * base_rate * cf * (1.04 if r.get("floors", 1) > 1 else 1)
    perim = 2 * (r.get("plot_w", 30) + r.get("plot_d", 40))
    b = {"Structure: materials": base * .55, "Structure: labor": base * .27, "Electrical": base * .07, "Plumbing": base * .06,
         "Interior": a * int_rate * cf, "Compound wall and gate": perim * 1400 * cf}
    if r.get("solar"): b["Solar (3 kW)"] = 180000
    if r.get("garden"): b["Landscaping"] = 80000
    sub = sum(b.values()); b["Approvals and fees (2%)"] = sub * .02; b["Contingency (7%)"] = sub * .07
    total = sum(b.values()); budget = r.get("budget")
    out = {"built_up_sqft": a, "tier": tier, "rate_per_sqft": round(total / a), "city_factor": cf,
           "items": {k: round(v) for k, v in b.items()}, "total": round(total), "low": round(total * .9), "high": round(total * 1.15),
           "budget": budget, "within_budget": (total <= budget) if budget else None, "gap": round(total - budget) if budget else None,
           "status": None, "suggestions": [],
           "note": "Range of -10% to +15% around the estimate. Rates vary by site, soil and market; get contractor quotes."}
    if budget: out["status"] = "within" if out["high"] <= budget else ("likely" if total <= budget else "over")
    if budget and total > budget and _sug and tier != "basic":
        sv = total - cost({**r, "quality": "basic"}, False)["total"]
        out["suggestions"] = [f"Switch to basic finishes: about {sv/1e5:.1f} lakh less", "Reduce built-up area or skip the second floor", "Phase interiors and solar for later"]
    return out

def timeline(r):
    s = max(1, r.get("floors", 1))
    return [{"phase": n, "weeks": w} for n, w in [("Foundation", 5), ("Structure", 8 * s), ("Roofing", 3),
            ("Electrical", 3), ("Plumbing", 3), ("Interior", 8), ("Finishing", 4)]]

def sustainability(r):
    t = ["Rainwater harvesting pit sized for the roof catchment",
         "Cross-ventilation: openings on opposite walls of living and bedrooms",
         "Deep sunshades on west-facing windows to cut afternoon heat"]
    t.append("3 kW rooftop solar is included in the estimate" if r.get("solar")
             else "Optional: add 3 kW rooftop solar to offset daytime load")
    return t

def interior(r):
    return {"theme": "Modern minimal" if r.get("modern") else "Warm contemporary",
            "colors": ["Off-white walls", "Teak accents", "Charcoal fixtures"],
            "lighting": ["Warm 3000K ambient", "Task lights in study and kitchen", "Large windows in living room"]}

def utilities(r):
    return {"electrical": ["Main DB near entrance", "Separate circuits for AC, kitchen, geyser",
                           "Solar inverter near DB" if r.get("solar") else "Provision for future solar"],
            "plumbing": ["Wet areas stacked on shared walls", "Overhead tank on roof", "Rainwater sump at the front setback"]}

def _explanation_en(r, c):
    p = [f"Your {'modern ' if r.get('modern') else ''}{r['bedrooms']} bedroom home has been designed for a {r.get('plot_w')} by {r.get('plot_d')} foot plot in {r['city']}.",
         "The living room is positioned at the front to maximize natural lighting."]
    if r.get("study"):
        p.append("The study overlooks the garden for a quieter workspace." if r.get("garden") else "The study is set away from the living room for quiet.")
    if r.get("vastu"): p.append("The pooja room is placed toward the north-east, following Vastu.")
    msg = f"The estimated cost is {c['total']/1e5:.1f} lakh rupees"
    if c["budget"]: msg += f", which is {'within' if c['within_budget'] else 'above'} your budget of {c['budget']/1e5:.0f} lakh"
    p.append(msg + ".")
    if c["within_budget"] is False: p.append("To save money, simplify interiors or reduce built-up area.")
    return " ".join(p)

def llm_explanation(r, c, fallback, lang="en"):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return fallback
    try:
        from openai import OpenAI
        resp = OpenAI(api_key=key).chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "system", "content": "Reply in the language with BCP-47 code " + lang + ". You are an architect. Explain this conceptual home design in under 90 words, spoken style, no lists."},
                      {"role": "user", "content": f"Requirements: {r}\nCost: {c}"}])
        return resp.choices[0].message.content
    except Exception:
        return fallback

EXPL = {  # intro, light, cost, within, over
 "hi": ("आपका {b} बेडरूम का घर {w} बाय {d} फ़ुट के प्लॉट के लिए डिज़ाइन किया गया है।", "लिविंग रूम आगे की ओर है ताकि भरपूर प्राकृतिक रोशनी मिले।", "अनुमानित लागत लगभग {c} लाख रुपये है।", "यह आपके {bud} लाख के बजट के भीतर है।", "यह आपके {bud} लाख के बजट से ज़्यादा है।"),
 "te": ("మీ {b} బెడ్రూమ్ ఇల్లు {w} బై {d} అడుగుల ప్లాట్ కోసం డిజైన్ చేయబడింది.", "సహజ కాంతి కోసం లివింగ్ రూమ్ ముందు భాగంలో ఉంది.", "అంచనా ఖర్చు సుమారు {c} లక్షల రూపాయలు.", "ఇది మీ {bud} లక్షల బడ్జెట్ లోపే ఉంది.", "ఇది మీ {bud} లక్షల బడ్జెట్ కంటే ఎక్కువ."),
 "ta": ("உங்கள் {b} படுக்கையறை வீடு {w} பை {d} அடி மனைக்காக வடிவமைக்கப்பட்டுள்ளது.", "இயற்கை வெளிச்சத்திற்காக வரவேற்பறை முன்பக்கம் உள்ளது.", "மதிப்பிடப்பட்ட செலவு சுமார் {c} லட்சம் ரூபாய்.", "இது உங்கள் {bud} லட்சம் பட்ஜெட்டுக்குள் உள்ளது.", "இது உங்கள் {bud} லட்சம் பட்ஜெட்டை விட அதிகம்."),
 "kn": ("ನಿಮ್ಮ {b} ಬೆಡ್‌ರೂಮ್ ಮನೆಯನ್ನು {w} ಬೈ {d} ಅಡಿ ನಿವೇಶನಕ್ಕೆ ವಿನ್ಯಾಸಗೊಳಿಸಲಾಗಿದೆ.", "ನೈಸರ್ಗಿಕ ಬೆಳಕಿಗಾಗಿ ಲಿವಿಂಗ್ ರೂಮ್ ಮುಂಭಾಗದಲ್ಲಿದೆ.", "ಅಂದಾಜು ವೆಚ್ಚ ಸುಮಾರು {c} ಲಕ್ಷ ರೂಪಾಯಿ.", "ಇದು ನಿಮ್ಮ {bud} ಲಕ್ಷ ಬಜೆಟ್ ಒಳಗಿದೆ.", "ಇದು ನಿಮ್ಮ {bud} ಲಕ್ಷ ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚು.")}

def explanation(r, c, lang="en"):
    t = EXPL.get(lang[:2])
    if not t: return _explanation_en(r, c)  # other languages: English text, or LLM-translated if OPENAI_API_KEY is set
    p = [t[0].format(b=r["bedrooms"], w=r.get("plot_w"), d=r.get("plot_d")), t[1], t[2].format(c=f"{c['total']/1e5:.1f}")]
    if c["budget"]: p.append((t[3] if c["within_budget"] else t[4]).format(bud=f"{c['budget']/1e5:.0f}"))
    return " ".join(p)