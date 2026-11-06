"""Architect Agent: architectural-style conceptual plan (walls, doors, windows, stairs) as SVG.
Layout: west strip | central hall | east strip, entrance at the front (south). Conceptual only."""
S = 12  # px per foot
W_ = {"Living": 3.4, "Dining": 2, "Kitchen": 2.2, "Master Bedroom": 3.2, "Bedroom": 2.6, "Bath": 1,
      "Study": 1.8, "Pooja": .8, "Utility": 1, "Stairs": .01, "Parking": 1}
MIN = {"Bath": 5, "Stairs": 9, "Pooja": 5, "Parking": 16, "Utility": 6}
DROP = ["Pooja", "Study", "Utility", "Dining"]
OPEN = {"Living", "Dining"}
CW = 3.5

def groups(r, floor, floors):
    b = r["bedrooms"]; g = []
    if floors == 1:
        g = [["Living", "Dining", "Kitchen"], ["Master Bedroom", "Bath"]] + [["Bedroom"]] * (b - 1) + ([["Bath"]] if b > 2 else [])
    elif floor == 0:
        g = [["Living", "Dining", "Kitchen"], ["Bedroom", "Bath"], ["Stairs"]]
    else:
        g = [["Master Bedroom", "Bath"]] + [["Bedroom", "Bath"]] * max(0, b - 2) + [["Stairs"]]
    if floor == 0 or floors == 1:
        if r.get("study"): g.insert(-1 if floors == 2 else len(g), ["Study"])
        if r.get("vastu"): g.insert(-1 if floors == 2 else len(g), ["Pooja"])
        if r.get("parking"): g.insert(1, ["Parking"])
    elif r.get("study"): g.insert(-1, ["Study"])
    return [list(x) for x in g]

def assign(gs):
    st = [g for g in gs if "Stairs" in g]; gs = [g for g in gs if "Stairs" not in g]
    s = {"W": [], "E": []}; used = {"W": 0, "E": 0}
    for g in gs:
        k = min(used, key=used.get); s[k] += g; used[k] += sum(MIN.get(n, 8) for n in g)
    for g in st: s["E"] += g
    return s

def alloc(names, L):
    mins = [MIN.get(n, 8) for n in names]; ws = [W_[n] for n in names]
    k = min(1, L / sum(mins)); extra = max(0, L - sum(mins))
    return [m * k + extra * w / sum(ws) for m, w in zip(mins, ws)]

def svg(r, floor=0):
    W, D, F = r.get("plot_w", 30), r.get("plot_d", 40), r.get("floors", 1)
    x0, y0, Wb, Db = 3.5, 4.0, W - 7, D - 10
    port = Db >= Wb
    Lb, Tb = (Db, Wb) if port else (Wb, Db)
    U, V = ((0, -1), (1, 0)) if port else ((1, 0), (0, 1))
    O = (x0, y0 + Db) if port else (x0, y0)
    P = lambda u, v: (O[0] + u * U[0] + v * V[0], O[1] + u * U[1] + v * V[1])
    vec = lambda a, b: (a * U[0] + b * V[0], a * U[1] + b * V[1])
    wl = (Tb - CW) / 2
    gs = groups(r, floor, F); merged = False; outdoor = False
    while True:
        st = assign(gs)
        if max(sum(MIN.get(n, 8) for n in s) for s in st.values()) <= Lb: break
        for d in DROP:
            hit = next((g for g in gs if d in g), None)
            if hit:
                if d == "Dining": hit.remove("Dining"); merged = True
                else: gs.remove(hit)
                break
        else:
            pk = next((g for g in gs if "Parking" in g), None)
            if pk: gs.remove(pk); outdoor = True
            else: break
    px = lambda p: (p[0] * S, p[1] * S)
    out = []
    def line(a, b, w=1, c="#111", extra=""):
        a, b = px(a), px(b); out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{c}" stroke-width="{w}" {extra}/>')
    def text(p, s, size=11, c="#111", weight="400"):
        p = px(p); out.append(f'<text x="{p[0]:.1f}" y="{p[1]:.1f}" text-anchor="middle" font-size="{size}" fill="{c}" font-weight="{weight}">{s}</text>')
    def rect(a, b, w, fill="none", dash=""):
        a, b = px(a), px(b); out.append(f'<rect x="{min(a[0],b[0]):.1f}" y="{min(a[1],b[1]):.1f}" width="{abs(a[0]-b[0]):.1f}" height="{abs(a[1]-b[1]):.1f}" fill="{fill}" stroke="#111" stroke-width="{w}" {dash}/>')
    # plot, garden
    rect((0, 0), (W, D), 1, "#fff", 'stroke-dasharray="6 4"')
    if r.get("garden") and floor == 0:
        rect((x0, y0 + Db + .6), (x0 + Wb, D - .6), 1, "#E4F0D8"); text((W / 2, y0 + Db + 3.6), "Garden", 11)
    if outdoor and floor == 0:
        rect((x0, y0 + Db + .6), (x0 + 9 * min(2, r.get("parking", 1)), D - .6), 1, "#EEE", 'stroke-dasharray="4 3"'); text((x0 + 4.5, y0 + Db + 3.6), "Parking", 10)
    rooms = []
    for k, names in st.items():
        ls = alloc(names, Lb); u = 0
        for n, l in zip(names, ls):
            rooms.append((n, k, u, l)); u += l
    for n, k, u, l in rooms:
        v0 = 0 if k == "W" else wl + CW
        a, b = P(u, v0), P(u + l, v0 + wl)
        rect(a, b, 2.5, "#fff", 'stroke-dasharray="5 3"' if n == "Parking" else "")
        c = P(u + l / 2, v0 + wl / 2)
        lab = "Living / Dining" if (n == "Living" and merged) else ("Car Porch" if n == "Parking" else n)
        text((c[0], c[1] - .2), lab, 11, weight="600"); text((c[0], c[1] + 1.2), f"{wl:.0f}' x {l:.0f}'", 9, "#666")
        if n == "Stairs":
            for i in range(1, int(l)): line(P(u + i, v0), P(u + i, v0 + wl), .8, "#555")
            text(P(u + l / 2, v0 + wl / 2 + 2.4), "UP" if floor == 0 and F == 2 else ("DN" if F == 2 else ""), 10, "#c00", "700")
    text(P(Lb / 2, wl + CW / 2), "Hall", 10, "#666")
    rect(P(0, 0), P(Lb, Tb), 9)
    def gap(a, b, w=9): line(a, b, w, "#fff")
    def door(h, t, n, w=3):
        a = (h[0] + t[0] * w, h[1] + t[1] * w); b = (h[0] + n[0] * w, h[1] + n[1] * w)
        gap(h, a, 6); line(h, b, 1.6)
        sw = 1 if t[0] * n[1] - t[1] * n[0] > 0 else 0
        pa, pb = px(a), px(b); out.append(f'<path d="M{pa[0]:.1f},{pa[1]:.1f} A{w*S},{w*S} 0 0 {sw} {pb[0]:.1f},{pb[1]:.1f}" fill="none" stroke="#111" stroke-width="1"/>')
    def win(c, t, l):
        a = (c[0] - t[0] * l / 2, c[1] - t[1] * l / 2); b = (c[0] + t[0] * l / 2, c[1] + t[1] * l / 2); n = (-t[1], t[0])
        gap(a, b, 9)
        for o in (-.22, 0, .22): line((a[0] + n[0] * o, a[1] + n[1] * o), (b[0] + n[0] * o, b[1] + n[1] * o), 1)
    for n, k, u, l in rooms:
        if n in ("Parking", "Stairs"): continue
        vw = wl if k == "W" else wl + CW; into = -1 if k == "W" else 1; uc = u + l / 2
        if n in OPEN: gap(P(uc - 2.5, vw), P(uc + 2.5, vw), 6)
        else: door(P(uc - 1.5, vw), vec(1, 0), vec(0, into))
        wl_len = min(4.5, l * .5) if n != "Bath" else 2
        win(P(uc, 0 if k == "W" else Tb), vec(1, 0), wl_len)
        if u < .01: win(P(0, wl / 2 if k == "W" else wl + CW + wl / 2), vec(0, 1), min(4, wl * .45))
        if u + l > Lb - .01: win(P(Lb, wl / 2 if k == "W" else wl + CW + wl / 2), vec(0, 1), min(4, wl * .45))
    door(P(0, wl + .3), vec(0, 1), vec(1, 0), CW - .6)
    text(P(-1.6, wl + CW / 2), "Entrance", 9, "#666")
    pad, top = 34, 46
    Wp, Hp = W * S + 2 * pad, D * S + pad + top
    title = ("Ground floor" if floor == 0 else "First floor") if F > 1 else "Floor plan"
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wp} {Hp}" font-family="Arial, sans-serif" style="background:#fff">'
            f'<text x="{pad}" y="30" font-size="17" font-weight="700" fill="#111">{title} <tspan font-size="11" font-weight="400" fill="#666">({W} x {D} ft plot)</tspan></text>'
            f'<g stroke="#c00" fill="#c00"><path d="M{Wp-pad-6},{top-8} l6,-18 l6,18 z"/></g><text x="{Wp-pad}" y="{top+6}" text-anchor="middle" font-size="12" font-weight="700" fill="#c00">N</text>'
            f'<g transform="translate({pad},{top})">')
    return head + "".join(out) + "</g></svg>"

def all_floors(r): return [svg(r, f) for f in range(r.get("floors", 1))]