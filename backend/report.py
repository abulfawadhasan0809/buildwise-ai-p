import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def build_pdf(p):
    buf = io.BytesIO(); s = getSampleStyleSheet(); r = p["requirements"]; c = p["cost"]
    d = [Paragraph("BuildWise AI - Conceptual Home Design", s["Title"]),
         Paragraph(f"Plot {r.get('plot_w')}x{r.get('plot_d')} ft, {r['city']}, {r['bedrooms']} BHK, {r['floors']} floor(s)", s["Normal"]),
         Spacer(1, 12), Paragraph("Design explanation", s["Heading2"]), Paragraph(p["explanation"], s["Normal"]),
         Paragraph("Cost estimate (INR)", s["Heading2"])]
    rows = [[k, f"{v:,}"] for k, v in c["items"].items()] + [["Total", f"{c['total']:,}"]]
    t = Table(rows, colWidths=[250, 120])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, colors.grey), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
    d += [t, Paragraph("Construction timeline", s["Heading2"])]
    d += [Paragraph(f"{x['phase']}: {x['weeks']} weeks", s["Normal"]) for x in p["timeline"]]
    d += [Paragraph("Sustainability", s["Heading2"])] + [Paragraph("- " + x, s["Normal"]) for x in p["sustainability"]]
    d += [Spacer(1, 12), Paragraph("Conceptual design only. Not for construction. Consult a licensed architect and structural engineer.", s["Italic"])]
    SimpleDocTemplate(buf, pagesize=A4).build(d)
    return buf.getvalue()
