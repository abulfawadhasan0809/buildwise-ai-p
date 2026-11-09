"""Consultant Agent: turns a transcript into a structured requirement document."""
import re, unicodedata

KW = {  # native-script words -> English tokens (Hindi, Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia)
 "lakh": "लाख లక్ష லட்சம் ಲಕ್ಷ ലക്ഷം লক্ষ લાખ ਲੱਖ ଲକ୍ଷ", "crore": "करोड़ करोड కోటి கோடி ಕೋಟಿ കോടി কোটি કરોડ ਕਰੋੜ",
 "bhk": "बेडरूम बीएचके బెడ్రూమ్ బీహెచ్కె படுக்கையறை பிஎச்கே ಬೆಡ್ರೂಮ್ ബെഡ്റൂം শোবার", "vastu": "वास्तु వాస్తు வாஸ்து ವಾಸ್ತು വാസ്തു বাস্তু વાસ્તુ",
 "garden": "बगीचा बाग गार्डन తోట గార్డెన్ தோட்டம் கார்டன் ತೋಟ ಗಾರ್ಡನ್", "parking": "पार्किंग పార్కింగ్ பார்க்கிங் ಪಾರ್ಕಿಂಗ್", "solar": "सोलर సోలార్ சோலார் ಸೋಲಾರ್",
 "study": "स्टडी", "duplex": "डुप्लेक्स డూప్లెక్స్ டூப்ளெக்ஸ்", "x": "बाई बाय బై பை ಬೈ", "yes": "हाँ हां అవును ஆம் ಹೌದು അതെ", "no": "नहीं కాదు இல்லை ಇಲ್ಲ ഇല്ല",
 "one": "एक ఒక்క", "two": "दो రెండు", "three": "तीन మూడు", "four": "चार నాలుగు", "five": "पांच ఐదు"}
WORDS = {w: en for en, ws in KW.items() for w in ws.split()}

def norm(text):
    t = "".join(str(unicodedata.digit(c)) if c.isdigit() and not c.isascii() else c for c in text)
    t = re.sub(r"[,;।?!]|\.(?=\s|$)", " ", t)
    return " ".join(WORDS.get(w, w) for w in t.split())

def extract(text: str, prev: dict | None = None) -> dict:
    t = norm(text).lower().replace("×", "x").replace("*", "x")
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
    if re.search(r"luxury|premium|high.?end", t): r["quality"] = "premium"
    elif re.search(r"budget.friendly|basic|low.?cost|affordable|economy", t): r["quality"] = "basic"
    r.setdefault("city", "Hyderabad"); r.setdefault("bedrooms", 3)
    return r

Q = {"en": ("What are your plot dimensions, for example 30 by 40 feet?", "What is your total budget for construction?", "Would you like Vastu compliance?"),
     "hi": ("आपके प्लॉट का आकार क्या है, जैसे 30 बाय 40 फ़ीट?", "आपका कुल बजट कितना है?", "क्या आप वास्तु के अनुसार डिज़ाइन चाहते हैं?"),
     "te": ("మీ ప్లాట్ పరిమాణం ఎంత, ఉదాహరణకు 30 బై 40 అడుగులు?", "మీ మొత్తం బడ్జెట్ ఎంత?", "మీకు వాస్తు ప్రకారం డిజైన్ కావాలా?"),
     "ta": ("உங்கள் மனையின் அளவு என்ன, எடுத்துக்காட்டாக 30 பை 40 அடி?", "உங்கள் மொத்த பட்ஜெட் எவ்வளவு?", "வாஸ்து படி வடிவமைப்பு வேண்டுமா?"),
     "kn": ("ನಿಮ್ಮ ನಿವೇಶನದ ಅಳತೆ ಎಷ್ಟು, ಉದಾಹರಣೆಗೆ 30 ಬೈ 40 ಅಡಿ?", "ನಿಮ್ಮ ಒಟ್ಟು ಬಜೆಟ್ ಎಷ್ಟು?", "ವಾಸ್ತು ಪ್ರಕಾರ ವಿನ್ಯಾಸ ಬೇಕೇ?")}

def follow_up(r: dict, lang: str = "en") -> str | None:
    q = Q.get(lang[:2], Q["en"])
    if "plot_w" not in r: return q[0]
    if "budget" not in r: return q[1]
    if "vastu" not in r: return q[2]
    return None