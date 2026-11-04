"""Architect Agent: slice-and-dice room layout rendered as SVG. Conceptual only."""
COLORS = {"Living": "#F7E7B4", "Kitchen": "#F4C7A1", "Dining": "#E8D5B5", "Bedroom": "#C9DDEB",
          "Master Bedroom": "#B5CFE3", "Bath": "#BFE3DC", "Study": "#D9D2EE", "Parking": "#D5D8DB",
          "Garden": "#CDE8B8", "Pooja": "#F9D6D6", "Utility": "#E3E3E3", "Stairs": "#EAEAEA"}

def rooms_for(r, floor, floors):
    beds = r["bedrooms"]
    if floors == 1:
        L = [("Living", 3), ("Kitchen", 2), ("Dining", 1.6), ("Master Bedroom", 3), ("Bath", 1)]
        L += [("Bedroom", 2.5)] * (beds - 1) + [("Bath", 1)] * max(0, beds - 2)
        if r.get("study"): L.append(("Study", 1.6))
        if r.get("vastu"): L.append(("Pooja", .7))
        if r.get("parking"): L.append(("Parking", 2.5 * min(r["parking"], 2)))
        return L
    if floor == 0:
        L = [("Living", 3), ("Kitchen", 2), ("Dining", 1.6), ("Bedroom", 2.5), ("Bath", 1), ("Stairs", .8)]
        if r.get("parking"): L.append(("Parking", 2.5 * min(r["parking"], 2)))
        if r.get("study"): L.append(("Study", 1.6))
        if r.get("vastu"): L.append(("Pooja", .7))
        return L
    n = max(1, beds - 1)
    return [("Master Bedroom", 3)] + [("Bedroom", 2.5)] * (n - 1) + [("Bath", 1)] * n + [("Stairs", .8), ("Utility", 1)]

def _split(items, x, y, w, h, out, vert=True):
    if len(items) == 1:
        out.append((items[0][0], x, y, w, h)); return
    tot = sum(i[1] for i in items); acc = 0; k = 0
    for k, i in enumerate(items):
        acc += i[1]
        if acc >= tot / 2: break
    k = min(k, len(items) - 2); a, b = items[:k + 1], items[k + 1:]
    f = sum(i[1] for i in a) / tot
    if vert:
        _split(a, x, y, w * f, h, out, False); _split(b, x + w * f, y, w * (1 - f), h, out, False)
    else:
        _split(a, x, y, w, h * f, out, True); _split(b, x, y + h * f, w, h * (1 - f), out, True)

def svg(r, floor=0):
    W, D, F = r.get("plot_w", 30), r.get("plot_d", 40), r.get("floors", 1)
    S, m = 14, 3
    pw, pd = W * S, D * S
    gh = D * 0.18 if (r.get("garden") and floor == 0) else 0
    out = []
    _split(rooms_for(r, floor, F), m * S, (m + gh) * S, (W - 2 * m) * S, (D - 2 * m - gh) * S, out)
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {pw} {pd + 28}" font-family="sans-serif">',
         f'<rect width="{pw}" height="{pd}" fill="#FAFBFA" stroke="#14213D" stroke-width="2" stroke-dasharray="6 4"/>']
    if gh:
        p.append(f'<rect x="{m*S}" y="{m*S}" width="{(W-2*m)*S}" height="{gh*S}" fill="{COLORS["Garden"]}" stroke="#14213D"/>'
                 f'<text x="{pw/2}" y="{(m+gh/2)*S}" text-anchor="middle" font-size="13" fill="#14213D">Garden</text>')
    for n, x, y, w, h in out:
        p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{COLORS.get(n, "#eee")}" stroke="#14213D" stroke-width="2"/>'
                 f'<text x="{x+w/2:.1f}" y="{y+h/2:.1f}" text-anchor="middle" font-size="12" fill="#14213D">{n}</text>')
    p.append(f'<text x="{pw/2}" y="{pd+18}" text-anchor="middle" font-size="12" fill="#14213D">{W} x {D} ft plot, floor {floor+1}. Conceptual only.</text></svg>')
    return "".join(p)

def all_floors(r): return [svg(r, f) for f in range(r.get("floors", 1))]
