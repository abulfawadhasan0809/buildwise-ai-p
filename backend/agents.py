"""Cost, sustainability, timeline, interior, utility and explanation agents."""
import os

def built_area(r):
    return int(r.get("plot_w", 30) * r.get("plot_d", 40) * 0.65 * r.get("floors", 1))

def cost(r):
    a = built_area(r); rate = 2000 if r.get("modern") else 1800  # INR/sqft, rough Hyderabad ballpark
    base = a * rate
    b = {"Material": base * .50, "Labor": base * .25, "Electrical": base * .07, "Plumbing": base * .06,
         "Interior": a * (900 if r.get("modern") else 600)}
    if r.get("solar"): b["Solar (3 kW)"] = 180000
    if r.get("garden"): b["Landscaping"] = 80000
    total = sum(b.values()); budget = r.get("budget")
    return {"built_up_sqft": a, "rate_per_sqft": rate, "items": {k: round(v) for k, v in b.items()},
            "total": round(total), "budget": budget,
            "within_budget": (total <= budget) if budget else None,
            "gap": round(total - budget) if budget else None,
            "note": "Rough order-of-magnitude estimate. Get quotes from local contractors."}

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

def explanation(r, c):
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

def llm_explanation(r, c, fallback):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return fallback
    try:
        from openai import OpenAI
        resp = OpenAI(api_key=key).chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "system", "content": "You are an architect. Explain this conceptual home design in under 90 words, spoken style, no lists."},
                      {"role": "user", "content": f"Requirements: {r}\nCost: {c}"}])
        return resp.choices[0].message.content
    except Exception:
        return fallback
