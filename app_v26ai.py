# ============================================================
# Timber AI Assistant V26-AI — PART 1 of 3
# CONFIG & DATA
# Paste this FIRST at the top of your app.py in GitHub
# ============================================================

import streamlit as st
import math
import json
import requests
import re
from datetime import datetime

st.set_page_config(layout="wide", page_title="Timber AI Assistant V26-AI", page_icon="🪵")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.app-header {
    border-left: 4px solid #1D9E75;
    padding: 14px 20px;
    background: var(--background-color);
    border-radius: 10px;
    border: 0.5px solid #e0e0e0;
    border-left-width: 4px;
    margin-bottom: 1rem;
}
.app-header-title { font-size: 22px; font-weight: 600; color: inherit; display: flex; align-items: center; gap: 10px; }
.app-header-sub { font-size: 13px; color: #888; margin-top: 4px; }
.stButton button[kind="primary"] { background-color:#10b981!important; color:white!important; }
.stButton button[kind="primary"]:hover { background-color:#059669!important; }
.stTextArea textarea { font-family:'Calibri','Segoe UI',sans-serif!important; font-size:14px!important; line-height:1.7!important; }
.staff-log { background: #fafafa; border: 1px solid #e8e8e8; border-radius: 10px; overflow: hidden; }
.staff-log-header { background: #1D9E75; color: white; font-size: 13px; font-weight: 600; padding: 8px 16px; letter-spacing: 0.03em; }
.log-item { padding: 10px 16px; border-bottom: 0.5px solid #eee; }
.log-item:last-child { border-bottom: none; }
.log-item-head { font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 6px; display:flex; align-items:center; gap:8px; }
.log-num { background:#E1F5EE; color:#0F6E56; font-size:11px; font-weight:600; width:20px; height:20px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; }
.log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 20px; font-size: 13px; }
.log-label { color: #888; }
.log-val { color: #1a1a1a; font-weight: 500; }
.log-profit { color: #0F6E56; font-weight: 600; }
.log-total { padding: 10px 16px; background: #E1F5EE; display: flex; justify-content: space-between; align-items: center; }
.log-total-label { font-size: 14px; color: #0F6E56; font-weight: 600; }
.log-total-val { font-size: 20px; font-weight: 700; color: #0F6E56; }
.profit-chip { background:#EAF3DE; color:#3B6D11; font-size:11px; padding:1px 7px; border-radius:99px; margin-left:5px; }
.warn-chip { background:#FAEEDA; color:#854F0B; font-size:13px; font-weight:600; padding:3px 10px; border-radius:99px; margin-left:5px; }
.sup-header { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.sup-avatar { width:44px; height:44px; border-radius:50%; background:#E1F5EE; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:600; color:#0F6E56; flex-shrink:0; }
.sup-name { font-size:18px; font-weight:600; color:inherit; }
.sup-sub { font-size:12px; color:#888; margin-top:2px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTS
# ============================================================
SPECIES   = ["Kapur", "Balau", "Chengal", "Mixed Keruing", "Pure Keruing"]
SMALL_QTY = 10
FULL_W    = 1220   # standard sheet width mm
FULL_L    = 2440   # standard sheet length mm

inch_to_mm = {1:20, 2:43, 3:70, 4:93, 5:117, 6:143, 7:168, 8:193, 9:218, 10:243, 12:293}

PLY_GRADES = [
    "MR China", "WBP (TA)", "BB/CC Furniture",
    "Casting Black China", "Casting Black Vietnam",
    "Marine BS1088", "T2 Marine", "Fire Retardant BS476"
]

# ============================================================
# PLYWOOD PRICE TABLES
# ============================================================
PLY_SELL = {
    "MR China":              {3:3.25,   6:6.63,   9:9.36,   12:14.04,  15:19.0,   18:21.63},
    "WBP (TA)":              {6:11.31,  9:15.6,   12:18.46, 15:26.4,   18:27.5,   25:39.0},
    "BB/CC Furniture":       {3:5.72,   6:14.3,   9:16.75,  12:21.0,   15:26.4,   18:30.84, 25:44.04},
    "Casting Black China":   {12:18.84, 18:22.08},
    "Casting Black Vietnam": {12:19.625,18:25.2},
    "Marine BS1088":         {9:36.0,   12:45.96, 15:52.0,  18:63.0,   25:84.0},
    "T2 Marine":             {6:21.0,   9:24.0,   12:31.2,  15:37.2,   18:43.2,   25:57.6},
    "Fire Retardant BS476":  {3:40.0,   6:52.0,   9:74.0,   12:93.0,   15:102.0,  18:120.0, 25:150.0},
}
PLY_COST = {
    "MR China":              {3:2.5,    6:5.1,    9:7.2,    12:10.8,   15:15.2,   18:17.3},
    "WBP (TA)":              {6:8.7,    9:12.0,   12:14.2,  15:22.0,   18:22.0,   25:32.5},
    "BB/CC Furniture":       {3:4.4,    6:11.0,   9:13.4,   12:16.8,   15:22.0,   18:25.7,  25:36.7},
    "Casting Black China":   {12:15.7,  18:18.4},
    "Casting Black Vietnam": {12:15.7,  18:21.0},
    "Marine BS1088":         {9:30.0,   12:38.3,  15:46.2,  18:56.7,   25:77.7},
    "T2 Marine":             {6:17.5,   9:20.0,   12:26.0,  15:31.0,   18:36.0,   25:48.0},
    "Fire Retardant BS476":  {3:14.0,   6:26.0,   9:37.0,   12:49.0,   15:63.0,   18:70.0,  25:80.0},
}
PLY_ACTUAL = {
    "MR China":        {3: "actual +-1.8mm (China)"},
    "BB/CC Furniture": {3: "actual +-2.2mm"},
}
PLY_MOQ = {
    "MR China":              {3: 10},
    "WBP (TA)":              {},
    "BB/CC Furniture":       {3: 10},
    "Casting Black China":   {},
    "Casting Black Vietnam": {},
    "Marine BS1088":         {},
    "T2 Marine":             {},
    "Fire Retardant BS476":  {3: 10},
}

# ============================================================
# SPECIES MAP — FIX 2: pure/mixed keruing before plain keruing
# ============================================================
SPECIES_MAP = {
    "pure keruing":  "Pure Keruing",
    "mixed keruing": "Mixed Keruing",
    "keruing":       "Mixed Keruing",
    "chengal":"Chengal","chengai":"Chengal","chenggal":"Chengal",
    "kapur":"Kapur","kapor":"Kapur",
    "balau":"Balau","balu":"Balau",
    "坡楼":"Chengal","柚木":"Chengal","重坡楼":"Chengal",
    "山樟":"Kapur","樟木":"Kapur","卡布":"Kapur",
    "芭劳":"Balau","巴劳":"Balau","八劳":"Balau",
    "克鲁英":"Mixed Keruing","苦楝":"Mixed Keruing","克鲁":"Mixed Keruing",
}

# ============================================================
# SESSION STATE — initialised once at startup
# ============================================================
_defaults = {
    "order_items": [], "odd_items": [], "ply_items": [],
    "sel_grade":   "MR China",
    "odd_cthk": None, "odd_cwid": None, "odd_clen": None,
    "odd_qthk": None, "odd_qwid": None, "odd_qlen": None,
    "odd_sp":  "Kapur",
    "odd_ctu": "mm", "odd_cwu": "mm", "odd_clu": "m",
    "odd_qtu": "mm", "odd_qwu": "mm", "odd_qlu": "m",
    "odd_qty": 1,
    "cust_name": "", "cust_mobile": "",
    "q_ready":   False, "q_reply":   "", "q_total":   0.0, "q_cost":   0.0, "q_nitem": 0, "q_log":   [],
    "odd_ready": False, "odd_reply": "", "odd_total": 0.0, "odd_cost": 0.0, "odd_nitem":0, "odd_log": [],
    "ply_ready": False, "ply_reply": "", "ply_total": 0.0, "ply_cost": 0.0, "ply_nitem":0, "ply_log": [],
    "cut_ready": False, "cut_reply": "", "cut_total": 0.0, "cut_cost": 0.0,
    "ai_parsed": [], "ai_input": "", "ai_ran": False,
    "hist_search_val": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def reset_all():
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="app-header">
  <div class="app-header-title">🪵 Timber AI Assistant
    <span style="background:#1D9E75;color:white;font-size:13px;padding:2px 8px;border-radius:99px;margin-left:8px;vertical-align:middle">AI</span>
  </div>
  <div class="app-header-sub">Professional Quoting System &nbsp;·&nbsp; Prices in SGD &nbsp;·&nbsp; AI-Powered Quote Parser</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# RATE INPUTS — live widgets, used by all tabs
# ============================================================
st.subheader("Current Rates (SGD/ton)")
rc1, rc2, rc3, rc4, rc5 = st.columns(5)
with rc1: kapur_rate    = st.number_input("Kapur",         min_value=0, value=3800, step=50, key="r_kapur")
with rc2: balau_rate    = st.number_input("Balau",         min_value=0, value=5500, step=50, key="r_balau")
with rc3: cheng_rate    = st.number_input("Chengal",       min_value=0, value=6000, step=50, key="r_cheng")
with rc4: mkeruing_rate = st.number_input("Mixed Keruing", min_value=0, value=650,  step=50, key="r_mker")
with rc5: pkeruing_rate = st.number_input("Pure Keruing",  min_value=0, value=1000, step=50, key="r_pker")

species_rate = {
    "Kapur": kapur_rate, "Balau": balau_rate, "Chengal": cheng_rate,
    "Mixed Keruing": mkeruing_rate, "Pure Keruing": pkeruing_rate
}
st.divider()

# ============================================================
# END OF PART 1 — paste Part 2 immediately below this line
# ============================================================
# ============================================================
# Timber AI Assistant V26-AI — PART 2 of 3
# FUNCTIONS: Gist helpers, calc engine, parser, UI utilities
# Paste this SECOND, immediately after Part 1
# ============================================================

# ============================================================
# GITHUB GIST HELPERS
# ============================================================
def gist_headers():
    token = st.secrets.get("github_token", "")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def load_history():
    gist_id = st.secrets.get("gist_id", "")
    if not gist_id: return []
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}",
                         headers=gist_headers(), timeout=15)
        if r.status_code == 200:
            files = r.json().get("files", {})
            if "timber_quotes.json" not in files: return []
            raw = files["timber_quotes.json"]["content"]
            if not raw or raw.strip() == "[]": return []
            return json.loads(raw)
        elif r.status_code == 401:
            st.warning("⚠️ GitHub token expired. Please update in Streamlit secrets.")
        elif r.status_code == 404:
            st.warning("⚠️ Gist not found. Please check gist_id in Streamlit secrets.")
    except Exception as e:
        st.warning(f"⚠️ Could not load history: {str(e)}")
    return []

def save_history(history):
    gist_id = st.secrets.get("gist_id", "")
    token   = st.secrets.get("github_token", "")
    if not gist_id: st.error("❌ gist_id not set in Streamlit secrets."); return False
    if not token:   st.error("❌ github_token not set in Streamlit secrets."); return False
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=gist_headers(),
            json={"files": {"timber_quotes.json": {"content": json.dumps(history, indent=2)}}},
            timeout=15)
        if r.status_code == 200: return True
        elif r.status_code == 401: st.error("❌ GitHub token expired or invalid."); return False
        elif r.status_code == 404: st.error("❌ Gist not found."); return False
        else: st.error(f"❌ Could not save. Status: {r.status_code}"); return False
    except Exception as e:
        st.error(f"❌ Network error: {str(e)}"); return False

def save_quote(customer, mobile, total, items, quote_text, cost_total=0, quote_type="Quote"):
    history = load_history()
    profit  = round(total - cost_total, 2)
    margin  = round((profit / total * 100), 1) if total > 0 else 0
    entry   = {
        "id":       datetime.now().strftime("%Y%m%d_%H%M%S"),
        "date":     datetime.now().strftime("%d %b %Y"),
        "time":     datetime.now().strftime("%H:%M"),
        "customer": customer.strip() if customer.strip() else "—",
        "mobile":   mobile.strip()   if mobile.strip()   else "—",
        "type":     quote_type,
        "items": items, "total": total, "cost": cost_total,
        "profit": profit, "margin": margin, "text": quote_text
    }
    history.insert(0, entry)
    history = history[:200]
    return save_history(history)

def delete_quote(qid):
    history = load_history()
    save_history([q for q in history if q.get("id") != qid])

# ============================================================
# CALC FUNCTIONS
# ============================================================
def mm_to_inch(mm):
    for inch, val in inch_to_mm.items():
        if abs(mm - val) <= 6: return inch
    return max(round(mm / 25.4), 1)

def m_to_ft(m):
    if m <= 2.4:   return 8
    elif m <= 3.0: return 10
    elif m <= 3.6: return 12
    elif m <= 4.2: return 14
    else:          return round(m * 3.28084)

def calc(thk, wid, length, rate):
    raw = 7200 / (thk * wid * length)
    pcs = max(math.floor(raw), 1)
    return round(raw, 3), pcs, round(rate / pcs, 2)

def is_keruing(species):
    return species in ["Mixed Keruing", "Pure Keruing"]

def build_reply(lines, total, is_timber=True, extra_note=""):
    out = list(lines)
    out.append(f"\nTotal : S${total:,.2f}")
    out.append("\nTolerances:")
    out.append("- Thickness/Width: +-1~2mm")
    if is_timber:
        out.append("- Length: +-25~50mm")
    if extra_note:
        out.append(extra_note)
    out.append("\nDelivery / Self Collection:")
    out.append("30 Kranji Loop (Blk A) #04-05")
    out.append("TimMac @ Kranji S739570")
    return "\n".join(out)

# ============================================================
# UI RENDER HELPERS
# ============================================================
def render_table(rows):
    if not rows: return
    headers = list(rows[0].keys())
    html = '<table style="width:100%;border-collapse:collapse;font-size:13px">'
    html += '<thead><tr>' + ''.join(
        f'<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #1D9E75;color:#555;font-weight:500">{h}</th>'
        for h in headers) + '</tr></thead><tbody>'
    for i, row in enumerate(rows):
        bg = "#f9fdf9" if i % 2 == 0 else "white"
        html += f'<tr style="background:{bg}">' + ''.join(
            f'<td style="padding:6px 10px;border-bottom:0.5px solid #eee">{row[h]}</td>'
            for h in headers) + '</tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

def render_staff_log(log_items, grand_total, cost_total):
    profit = round(grand_total - cost_total, 2)
    margin = round((profit / grand_total * 100), 1) if grand_total > 0 else 0
    html = '<div class="staff-log"><div class="staff-log-header">Staff Calculation Log</div>'
    for i, item in enumerate(log_items, 1):
        warn    = '<span class="warn-chip">&#9888;&#65039; SMALL QTY &mdash; adjust price before sending</span>' if item.get("small_qty") else ""
        grid    = "".join(f'<span class="log-label">{k}</span><span class="log-val">{v}</span>' for k, v in item["rows"].items())
        moq_div = f'<div style="background:#FAEEDA;color:#854F0B;font-size:13px;font-weight:600;padding:4px 12px;border-radius:6px;margin-top:4px">&#9888;&#65039; MOQ APPLIED &mdash; {item.get("moq_note","")}</div>' if item.get("moq_flag") else ""
        html += '<div class="log-item">'
        html += f'<div class="log-item-head"><span class="log-num">{i}</span>{item["heading"]}</div>'
        html += f'<div class="log-grid">{grid}<span class="log-label">Profit</span>'
        html += f'<span class="log-profit">{item.get("profit_line","")} <span class="profit-chip">{item.get("margin_pct","")}</span>{warn}</span></div>'
        html += moq_div + '</div>'
    html += '<div class="log-total">'
    html += f'<div class="log-total-label">Grand total &nbsp;&middot;&nbsp; {len(log_items)} item(s) &nbsp;&middot;&nbsp; Margin {margin}%</div>'
    html += f'<div><span class="log-total-val">S${grand_total:,.2f}</span> <span class="profit-chip">Profit S${profit:,.2f}</span></div>'
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# ============================================================
# PARSER FUNCTIONS
# ============================================================
def detect_species(text):
    t = text.lower().strip()
    for k, v in SPECIES_MAP.items():
        if k in t: return v
    return None

def is_word(s):
    """True if string is purely alphabetic (Latin or CJK) — not digits or symbols."""
    return bool(re.match(r'^[a-zA-Z\u4e00-\u9fff]+$', s))

def normalize_to_mm(value, unit):
    u = (unit or "").lower().strip()
    if u in ["mm","毫米",""]:   return float(value)
    if u in ["cm","厘米"]:       return float(value) * 10
    if u in ["m","米"]:          return float(value) * 1000
    if u in ["ft","feet","'"]:  return float(value) * 304.8
    if u in ["in","inch",'"']: return float(value) * 25.4
    return float(value)

# FIX 4: threshold raised 500→600 so 500mm widths are not misread as lengths
def classify_dim(val_mm):
    if val_mm >= 600: return "length"
    if val_mm >= 80:  return "width"
    return "thickness"

def extract_qty(text):
    patterns = [
        r"(?:qty|quantity)\s*[:\-]?\s*(\d+)",
        r"(\d+)\s*(?:pcs|pieces|pc|支|条|块|根)",
        r"(?:pcs|pieces|pc|支|条|块|根)\s*[:\-]?\s*(\d+)",
        r"[xX×]\s*(\d+)\s*$",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m: return int(m.group(1))
    return None

def parse_smart_text(text):
    results = []
    lines   = text.strip().split("\n")
    cur_sp  = None
    cur_thk = None
    cur_wid = None

    # Pre-pass: pick up species from first matching line
    for line in lines:
        sp = detect_species(line)
        if sp: cur_sp = sp; break

    i = 0
    while i < len(lines):
        line = lines[i].strip(); i += 1
        if not line: continue

        sp = detect_species(line)
        if sp: cur_sp = sp

        parts = re.split(r"[\s,\t]+", line)

        # FIX 5: two-word species only when BOTH parts[0] and parts[1] are alphabetic
        sp_from_parts = None
        num_offset    = 1
        if len(parts) >= 2 and is_word(parts[0]) and is_word(parts[1]):
            candidate = detect_species(parts[0] + " " + parts[1])
            if candidate:
                sp_from_parts = candidate
                num_offset    = 2
        if not sp_from_parts and is_word(parts[0]):
            sp_from_parts = detect_species(parts[0])
            num_offset    = 1

        # Strategy 1: shorthand — species thk wid len qty (space-separated)
        if sp_from_parts and len(parts) >= num_offset + 4:
            try:
                thk = float(parts[num_offset])
                wid = float(parts[num_offset + 1])
                lm  = float(parts[num_offset + 2])
                qty = int(float(parts[num_offset + 3]))
                results.append({"species": sp_from_parts, "thk_mm": thk, "wid_mm": wid, "len_m": lm, "qty": qty})
                cur_sp = sp_from_parts; cur_thk = thk; cur_wid = wid
                continue
            except: pass

        # Strategy 2: labeled dims — e.g. 1080mm L x 300mm W x 70mm H
        labeled_pat     = r"(\d+\.?\d*)\s*(mm|cm|m|ft|in)?\s*[xX×]?\s*([LWHTDlwhtd])\b"
        labeled_matches = re.findall(labeled_pat, line)
        if len(labeled_matches) >= 2:
            dims = {}
            for val, unit, label in labeled_matches:
                vmm = normalize_to_mm(val, unit or "mm"); lb = label.upper()
                if lb == "L":              dims["length_mm"] = vmm
                elif lb == "W":            dims["width_mm"]  = vmm
                elif lb in ["H","T","D"]: dims["thk_mm"]    = vmm
            if "length_mm" in dims and "width_mm" in dims:
                dims.setdefault("thk_mm", min(dims["width_mm"], 100))
                sp_use = detect_species(line) or cur_sp or "Kapur"
                qty    = extract_qty(line)
                if not qty and i < len(lines):
                    qty = extract_qty(lines[i].strip()) or 1
                    if qty > 1: i += 1
                results.append({"species": sp_use, "thk_mm": dims["thk_mm"], "wid_mm": dims["width_mm"],
                                 "len_m": round(dims["length_mm"] / 1000, 3), "qty": qty})
                cur_thk = dims["thk_mm"]; cur_wid = dims["width_mm"]
                continue

        # Strategy 3: length=qty pairs — e.g. 2400=36支 1500=16支 (inherits cur thk/wid)
        lq_all = re.findall(r"(\d{3,5})\s*[=:]\s*(\d+)\s*(?:支|条|块|pcs|pc|pieces)?", line)
        if lq_all and cur_thk and cur_wid:
            sp_use = detect_species(line) or cur_sp or "Kapur"; added = 0
            for lstr, qstr in lq_all:
                lmm = float(lstr)
                if lmm < 200: continue
                results.append({"species": sp_use, "thk_mm": cur_thk, "wid_mm": cur_wid,
                                 "len_m": round(lmm / 1000, 3), "qty": int(qstr)})
                added += 1
            if added: continue

        # Strategy 4: two dims only — e.g. 35x80 (sets context, waits for lengths)
        two_pat = r"^[^=:\d]*(\d+\.?\d*)\s*(mm|cm)?\s*[xX×]\s*(\d+\.?\d*)\s*(mm|cm)?[^=:\d]*$"
        two_m   = re.match(two_pat, line)
        if two_m:
            v1 = normalize_to_mm(two_m.group(1), two_m.group(2) or "mm")
            v2 = normalize_to_mm(two_m.group(3), two_m.group(4) or "mm")
            cur_thk = min(v1, v2); cur_wid = max(v1, v2)
            continue

        # Strategy 5: three dims inline — e.g. 35x80x2400 (auto-classify by size)
        three_pat = r"(\d+\.?\d*)\s*(mm|cm|m|ft)?\s*[xX×]\s*(\d+\.?\d*)\s*(mm|cm|m|ft)?\s*[xX×]\s*(\d+\.?\d*)\s*(mm|cm|m|ft)?"
        three_m   = re.search(three_pat, line)
        if three_m:
            vals_mm = [
                normalize_to_mm(three_m.group(1), three_m.group(2) or "mm"),
                normalize_to_mm(three_m.group(3), three_m.group(4) or "mm"),
                normalize_to_mm(three_m.group(5), three_m.group(6) or "mm"),
            ]
            sv        = sorted(zip(vals_mm, [classify_dim(v) for v in vals_mm]), key=lambda x: -x[0])
            length_mm = next((v for v, c in sv if c == "length"),    sv[0][0])
            width_mm  = next((v for v, c in sv if c == "width"),     sv[1][0])
            thk_mm    = next((v for v, c in sv if c == "thickness"), sv[2][0])
            sp_use    = detect_species(line) or cur_sp or "Kapur"
            qty       = extract_qty(line) or 1
            results.append({"species": sp_use, "thk_mm": thk_mm, "wid_mm": width_mm,
                             "len_m": round(length_mm / 1000, 3), "qty": qty})
            cur_thk = thk_mm; cur_wid = width_mm
            continue

        # Strategy 6: Chinese metre notation — e.g. 35×80 2.4米 36支
        ch_m = re.search(r"(\d+\.?\d*)[×xX](\d+\.?\d*)\s+(\d+\.?\d*)米\s*(\d+)支", line)
        if ch_m:
            sp_use = detect_species(line) or cur_sp or "Kapur"
            t = float(ch_m.group(1)); w = float(ch_m.group(2))
            lm = float(ch_m.group(3)); qty = int(ch_m.group(4))
            results.append({"species": sp_use, "thk_mm": min(t, w), "wid_mm": max(t, w), "len_m": lm, "qty": qty})
            cur_thk = min(t, w); cur_wid = max(t, w)
            continue

        # Strategy 7: standalone qty — updates last item if it has default qty=1
        qty_only = extract_qty(line)
        if qty_only and results and results[-1].get("qty") == 1:
            results[-1]["qty"] = qty_only

    return results

# FIX 1: 2 args only — inch_to_mm removed from original buggy 3-arg call
# FIX 4: zero dimension guard prevents ZeroDivisionError
def parsed_to_order_item(p, species_rate_map):
    thk = p["thk_mm"]; wid = p["wid_mm"]; length_m = p["len_m"]; qty = p["qty"]; sp = p["species"]
    if thk <= 0 or wid <= 0 or length_m <= 0:
        raise ValueError(f"Invalid dimension: thk={thk}, wid={wid}, len={length_m}")
    thk_in = thk / 25.4; wid_in = wid / 25.4; len_ft = length_m * 3.28084
    raw       = 7200 / (thk_in * wid_in * len_ft)
    pcs_floor = max(math.floor(raw), 1)
    rate      = species_rate_map.get(sp, 3800)
    price     = round(rate / pcs_floor, 2)
    size_text = f"{thk}mm x {wid}mm x {length_m}m"
    return {
        "species": sp, "size": size_text, "thk": thk_in, "wid": wid_in, "length": round(len_ft, 2),
        "thk_mm": thk, "wid_mm": wid, "len_m": length_m, "price": price, "qty": qty,
        "line_total": round(price * qty, 2), "rate": rate, "pcs_per_ton": round(raw, 3),
        "small_qty": qty < SMALL_QTY
    }

def parsed_to_odd_item(p, species_rate_map):
    thk = p["thk_mm"]; wid = p["wid_mm"]; length_m = p["len_m"]; qty = p["qty"]; sp = p["species"]
    if thk <= 0 or wid <= 0 or length_m <= 0:
        raise ValueError(f"Invalid dimension: thk={thk}, wid={wid}, len={length_m}")
    thk_in = thk / 25.4; wid_in = wid / 25.4; len_ft = length_m * 3.28084
    raw       = 7200 / (thk_in * wid_in * len_ft)
    pcs_floor = max(math.floor(raw), 1)
    rate      = species_rate_map.get(sp, 3800)
    price     = round(rate / pcs_floor)
    cust_size = f"{thk}mm x {wid}mm x {length_m}m"
    return {
        "species": sp, "cust_size": cust_size, "quote_size": cust_size, "price": price, "qty": qty,
        "line_total": round(price * qty, 2), "rate": rate, "pcs_per_ton": round(raw, 4),
        "pcs_floor": pcs_floor, "small_qty": qty < SMALL_QTY
    }

# ============================================================
# END OF PART 2 — paste Part 3 immediately below this line
# ============================================================
# ============================================================
# Timber AI Assistant V26-AI — PART 3 of 3
# UI TABS: Quote Builder, Odd Size, Plywood, Suppliers, History, AI Parser
# Paste this THIRD, immediately after Part 2
# ============================================================

tab_quote, tab_odd, tab_ply, tab_sup, tab_hist, tab_ai = st.tabs([
    "📋 Quote Builder", "📐 Odd Size", "🪵 Plywood",
    "🏭 Suppliers", "🕘 History", "🤖 AI Parser"
])

# ============================================================
# TAB 1 — QUOTE BUILDER
# ============================================================
with tab_quote:
    st.markdown("#### Customer Details")
    cd1, cd2 = st.columns(2)
    with cd1:
        cust_name = st.text_input("Customer Name / Company",
            value=st.session_state.cust_name,
            placeholder="e.g. ABC Construction Pte Ltd", key="cust_name_inp")
        st.session_state.cust_name = cust_name
    with cd2:
        cust_mobile = st.text_input("Mobile Number",
            value=st.session_state.cust_mobile,
            placeholder="e.g. 9123 4567", key="cust_mobile_inp")
        st.session_state.cust_mobile = cust_mobile
    st.divider()
    st.subheader("Add Timber Item")
    st.caption("Rates above can be changed anytime before Generate Quote — price recalculates automatically.")

    with st.form("add_timber_form", clear_on_submit=True):
        fc1,fc2,fc3,fc4,fc5,fc6,fc7,fc8,fc9 = st.columns([2,1,1,1,1,1,1,1,1])
        with fc1: f_sp  = st.selectbox("Species", SPECIES, key="f_sp")
        with fc2: f_thk = st.number_input("Thickness", min_value=None, value=None, placeholder="e.g. 20",  step=1.0, format="%.1f", key="f_thk")
        with fc3: f_tu  = st.selectbox("Unit",   ["mm","inch"], key="f_tu")
        with fc4: f_wid = st.number_input("Width",     min_value=None, value=None, placeholder="e.g. 100", step=1.0, format="%.1f", key="f_wid")
        with fc5: f_wu  = st.selectbox("Unit ",  ["mm","inch"], key="f_wu")
        with fc6: f_len = st.number_input("Length",    min_value=None, value=None, placeholder="e.g. 2.4", step=0.1, format="%.1f", key="f_len")
        with fc7: f_lu  = st.selectbox("Unit  ", ["m","ft"], key="f_lu")
        with fc8: f_qty = st.number_input("Qty",       min_value=None, value=None, placeholder="e.g. 1",   step=1.0, format="%.0f", key="f_qty")
        with fc9:
            st.markdown("<br>", unsafe_allow_html=True)
            add_btn = st.form_submit_button("+ Add", use_container_width=True)

        if add_btn and f_thk and f_wid and f_len:
            f_qty_int = max(int(f_qty) if f_qty is not None else 1, 1)
            thk    = mm_to_inch(f_thk) if f_tu == "mm" else int(f_thk)
            wid    = mm_to_inch(f_wid) if f_wu == "mm" else int(f_wid)
            length = m_to_ft(f_len)    if f_lu == "m"  else int(f_len)
            if length == 19: length = 20
            rate = species_rate[f_sp]
            pcs_per_ton, pcs, price = calc(thk, wid, length, rate)
            if is_keruing(f_sp):
                size_text = f'{thk}" x {wid}" x {length}ft'
            else:
                mm_thk = inch_to_mm.get(thk, round(thk * 25.4))
                mm_wid = inch_to_mm.get(wid, round(wid * 25.4))
                size_text = f"{mm_thk}mm x {mm_wid}mm x {length}ft"
            st.session_state.order_items.append({
                "species": f_sp, "size": size_text, "thk": thk, "wid": wid, "length": length,
                "price": price, "qty": f_qty_int, "line_total": round(price * f_qty_int, 2),
                "rate": rate, "pcs_per_ton": pcs_per_ton, "small_qty": f_qty_int < SMALL_QTY
            })
            st.session_state.q_ready = False
            st.rerun()

    if st.session_state.order_items:
        for i, item in enumerate(st.session_state.order_items):
            cur_rate = species_rate[item["species"]]
            _, _, cur_price = calc(item["thk"], item["wid"], item["length"], cur_rate)
            cur_total = round(cur_price * item["qty"], 2)
            col_a, col_b, col_c = st.columns([3, 3, 1])
            with col_a: st.write(f"**{item['species']}**  {item['size']}")
            with col_b: st.write(f"S${cur_price}/pc  x  {item['qty']} pcs  =  S${cur_total:,.2f}")
            with col_c:
                if st.button("🗑️", key=f"dt_{i}"):
                    st.session_state.order_items.pop(i)
                    st.session_state.q_ready = False
                    st.rerun()

        st.divider()
        cg1, cg2 = st.columns([2, 1])
        with cg1: gen_quote = st.button("GENERATE QUOTE", type="primary", use_container_width=True)
        with cg2:
            if st.button("RESET ALL", use_container_width=True): reset_all()

        if gen_quote:
            log_items = []; customer_reply = []; grand_total = 0; cost_total = 0
            for item in st.session_state.order_items:
                cur_rate = species_rate[item["species"]]
                cur_ppt, _, cur_price = calc(item["thk"], item["wid"], item["length"], cur_rate)
                gt = round(cur_price * item["qty"], 2)
                grand_total += gt
                cost_est = round(gt * 0.85, 2); cost_total += cost_est
                profit = round(gt - cost_est, 2)
                margin_pct = round((profit / gt * 100), 1) if gt > 0 else 0
                log_items.append({
                    "heading": f"{item['species']} timber · {item['size']}",
                    "rows": {
                        "Rate":            f"S${cur_rate}/ton",
                        "Pieces per ton":  str(cur_ppt),
                        "Price per piece": f"S${cur_price}",
                        "Qty":             f"{item['qty']} pcs",
                        "Line total":      f"S${gt:,.2f}",
                    },
                    "profit_line": f"S${profit:,.2f}", "margin_pct": f"{margin_pct}%",
                    "small_qty": item["small_qty"]
                })
                customer_reply.append(
                    f"{item['species']} timber\n{item['size']} @ S${cur_price}/pcs x {item['qty']} = S${gt:,.2f}"
                )
            grand_total = round(grand_total, 2); cost_total = round(cost_total, 2)
            reply_text = build_reply(customer_reply, grand_total, is_timber=True)
            st.session_state.q_ready = True; st.session_state.q_reply  = reply_text
            st.session_state.q_total = grand_total; st.session_state.q_cost   = cost_total
            st.session_state.q_nitem = len(customer_reply); st.session_state.q_log = log_items

        if st.session_state.q_ready:
            grand_total = st.session_state.q_total; cost_total = st.session_state.q_cost
            st.subheader("Quote Summary")
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Items",       st.session_state.q_nitem)
            with m2: st.metric("Grand Total", f"S${grand_total:,.2f}")
            with m3: st.metric("Est. Profit", f"S${round(grand_total - cost_total, 2):,.2f}")
            with m4: st.metric("Est. Margin", f"{round((grand_total - cost_total) / grand_total * 100, 1) if grand_total > 0 else 0}%")
            render_staff_log(st.session_state.q_log, grand_total, cost_total)
            st.divider()
            st.subheader("Customer Reply (edit before sending)")
            edited_reply = st.text_area("", st.session_state.q_reply, height=350, key="cust_reply_q")
            a1, a2, a3 = st.columns(3)
            with a1:
                st.download_button("📥 Download TXT", data=edited_reply,
                    file_name=f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True)
            with a2:
                if st.button("💾 Save to History", type="primary", use_container_width=True, key="save_q"):
                    ok = save_quote(st.session_state.cust_name, st.session_state.cust_mobile,
                        grand_total, st.session_state.q_nitem, edited_reply, cost_total)
                    if ok: st.success("✅ Saved!")
                    else:  st.error("❌ Could not save.")
            with a3:
                st.download_button("📋 Copy as TXT", data=edited_reply,
                    file_name="quote_copy.txt", mime="text/plain", use_container_width=True)
    else:
        st.info("Add items above to build your order list.")
        if st.button("RESET ALL", use_container_width=True): reset_all()

# ============================================================
# TAB 2 — ODD SIZE
# ============================================================
with tab_odd:
    st.subheader("📐 Odd Size Timber")
    st.caption("Enter customer requested size AND your actual supply size. Pricing uses exact mm dimensions.")

    st.markdown("#### Customer Details")
    od_cd1, od_cd2 = st.columns(2)
    with od_cd1:
        odd_cust_name = st.text_input("Customer Name / Company",
            value=st.session_state.cust_name, placeholder="e.g. ABC Construction Pte Ltd", key="odd_cust_name_inp")
        st.session_state.cust_name = odd_cust_name
    with od_cd2:
        odd_cust_mobile = st.text_input("Mobile Number",
            value=st.session_state.cust_mobile, placeholder="e.g. 9123 4567", key="odd_cust_mobile_inp")
        st.session_state.cust_mobile = odd_cust_mobile
    st.divider()

    st.markdown("**Species, Rate & Quantity**")
    os1, os2, os3 = st.columns([2, 2, 1])
    with os1: st.session_state.odd_sp  = st.selectbox("Species", SPECIES, index=SPECIES.index(st.session_state.odd_sp), key="odd_sp_sel")
    with os2:
        odd_rate = st.number_input("Rate (S$/ton) — adjust if needed", min_value=0,
            value=species_rate[st.session_state.odd_sp], step=50, key="odd_rate")
    with os3: st.session_state.odd_qty = st.number_input("Qty (pcs)", min_value=1, value=st.session_state.odd_qty, step=1, key="odd_qty_inp")

    st.markdown("**Customer Requested Size**")
    cc1,cc2,cc3,cc4,cc5,cc6 = st.columns(6)
    with cc1: st.session_state.odd_cthk = st.number_input("Thickness", min_value=None, value=st.session_state.odd_cthk, placeholder="e.g. 80",  step=0.5, format="%.1f", key="odd_cthk_inp")
    with cc2: st.session_state.odd_ctu  = st.selectbox("Unit",  ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_ctu), key="odd_ctu_sel")
    with cc3: st.session_state.odd_cwid = st.number_input("Width",     min_value=None, value=st.session_state.odd_cwid, placeholder="e.g. 125", step=0.5, format="%.1f", key="odd_cwid_inp")
    with cc4: st.session_state.odd_cwu  = st.selectbox("Unit ", ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_cwu), key="odd_cwu_sel")
    with cc5: st.session_state.odd_clen = st.number_input("Length",    min_value=None, value=st.session_state.odd_clen, placeholder="e.g. 2.4", step=0.1, format="%.1f", key="odd_clen_inp")
    with cc6: st.session_state.odd_clu  = st.selectbox("Unit  ", ["m","ft"], index=["m","ft"].index(st.session_state.odd_clu), key="odd_clu_sel")

    st.markdown("**Your Quote Size (used for pricing)**")
    qc1,qc2,qc3,qc4,qc5,qc6 = st.columns(6)
    with qc1: st.session_state.odd_qthk = st.number_input("Thickness", min_value=None, value=st.session_state.odd_qthk, placeholder="e.g. 100", step=0.5, format="%.1f", key="odd_qthk_inp")
    with qc2: st.session_state.odd_qtu  = st.selectbox("Unit",  ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_qtu), key="odd_qtu_sel")
    with qc3: st.session_state.odd_qwid = st.number_input("Width",     min_value=None, value=st.session_state.odd_qwid, placeholder="e.g. 150", step=0.5, format="%.1f", key="odd_qwid_inp")
    with qc4: st.session_state.odd_qwu  = st.selectbox("Unit ", ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_qwu), key="odd_qwu_sel")
    with qc5: st.session_state.odd_qlen = st.number_input("Length",    min_value=None, value=st.session_state.odd_qlen, placeholder="e.g. 2.4", step=0.1, format="%.1f", key="odd_qlen_inp")
    with qc6: st.session_state.odd_qlu  = st.selectbox("Unit  ", ["m","ft"], index=["m","ft"].index(st.session_state.odd_qlu), key="odd_qlu_sel")

    ob1, ob2 = st.columns(2)
    with ob1:
        if st.button("+ Add to Odd Size List", type="primary", use_container_width=True):
            cthk=st.session_state.odd_cthk; cwid=st.session_state.odd_cwid; clen=st.session_state.odd_clen
            qthk=st.session_state.odd_qthk; qwid=st.session_state.odd_qwid; qlen=st.session_state.odd_qlen
            if cthk and cwid and clen and qthk and qwid and qlen:
                ctu=st.session_state.odd_ctu; cwu=st.session_state.odd_cwu; clu=st.session_state.odd_clu
                qtu=st.session_state.odd_qtu; qwu=st.session_state.odd_qwu; qlu=st.session_state.odd_qlu
                cust_size = f'{cthk}" x {cwid}" x {clen}{"ft" if clu=="ft" else "m"}' if ctu=="inch" else f"{cthk}mm x {cwid}mm x {clen}{clu}"
                if qtu == "inch":
                    q_thk_in=float(qthk); q_wid_in=float(qwid); quote_size=f'{qthk}" x {qwid}" x '
                else:
                    q_thk_in=float(qthk)/25.4; q_wid_in=float(qwid)/25.4; quote_size=f"{qthk}mm x {qwid}mm x "
                if qlu == "m":
                    q_length_ft=qlen*3.28084; quote_size+=f"{qlen}m"
                else:
                    q_length_ft=float(qlen); quote_size+=f"{qlen}ft"
                raw=7200/(q_thk_in*q_wid_in*q_length_ft)
                pcs_floor=max(math.floor(raw),1); price=round(odd_rate/pcs_floor)
                line_total=round(price*st.session_state.odd_qty,2)
                st.session_state.odd_items.append({
                    "species":st.session_state.odd_sp,"cust_size":cust_size,"quote_size":quote_size,
                    "price":price,"qty":st.session_state.odd_qty,"line_total":line_total,
                    "rate":odd_rate,"pcs_per_ton":round(raw,4),"pcs_floor":pcs_floor,
                    "small_qty":st.session_state.odd_qty<SMALL_QTY
                })
                st.session_state.odd_ready=False
                st.success(f"Added: {cust_size} → priced as {quote_size} @ S${price}/pc")
                st.rerun()
            else:
                st.error("Please fill in all size fields before adding.")
    with ob2:
        if st.button("Clear Inputs", use_container_width=True):
            for k in ["odd_cthk","odd_cwid","odd_clen","odd_qthk","odd_qwid","odd_qlen"]:
                st.session_state[k] = None
            st.rerun()

    if st.session_state.odd_items:
        st.divider()
        for i, item in enumerate(st.session_state.odd_items):
            oa, ob_col, oc, od = st.columns([3, 3, 1, 1])
            with oa:
                st.markdown(f"**{item['species']}**")
                st.caption(f"Customer: {item['cust_size']}  →  Priced as: {item['quote_size']}")
            with ob_col:
                st.markdown(f"S\\${item['price']}/pc &nbsp;×&nbsp; {item['qty']} =&nbsp; **S\\${item['line_total']:,.2f}**", unsafe_allow_html=True)
            with oc:
                if st.button("✏️", key=f"eo_{i}"):
                    st.session_state.odd_items.pop(i); st.session_state.odd_ready=False; st.rerun()
            with od:
                if st.button("🗑️", key=f"do_{i}"):
                    st.session_state.odd_items.pop(i); st.session_state.odd_ready=False; st.rerun()

        st.divider()
        og1, og2 = st.columns([2, 1])
        with og1: gen_odd = st.button("GENERATE ODD SIZE QUOTE", type="primary", use_container_width=True)
        with og2:
            if st.button("Clear List", use_container_width=True):
                st.session_state.odd_items=[]; st.session_state.odd_ready=False; st.rerun()

        if gen_odd:
            odd_log=[]; odd_reply=[]; odd_total=0; odd_cost=0
            for item in st.session_state.odd_items:
                odd_total+=item["line_total"]
                cost_est=round(item["line_total"]*0.85,2); odd_cost+=cost_est
                profit=round(item["line_total"]-cost_est,2)
                margin_pct=round((profit/item["line_total"]*100),1) if item["line_total"]>0 else 0
                odd_log.append({
                    "heading":f"{item['species']} (odd size)",
                    "rows":{
                        "Customer size":    item['cust_size'],
                        "Priced as":        item['quote_size'],
                        "Rate":             f"S${item['rate']}/ton",
                        "Pcs/ton (raw)":    str(item['pcs_per_ton']),
                        "Pcs used (floor)": str(item.get('pcs_floor',math.floor(float(item['pcs_per_ton'])))),
                        "Price per piece":  f"S${item['price']} (rounded to nearest $1)",
                        "Qty":              f"{item['qty']} pcs",
                        "Line total":       f"S${item['line_total']:,.2f}",
                    },
                    "profit_line":f"S${profit:,.2f}","margin_pct":f"{margin_pct}%","small_qty":item["small_qty"]
                })
                odd_reply.append(
                    f"{item['species']} timber\nYour size: {item['cust_size']}\n"
                    f"Supply size: {item['quote_size']}\n"
                    f"@ S${item['price']}/pcs x {item['qty']} = S${item['line_total']:,.2f}"
                )
            odd_total=round(odd_total,2); odd_cost=round(odd_cost,2)
            reply_text=build_reply(odd_reply,odd_total,is_timber=True)
            st.session_state.odd_ready=True; st.session_state.odd_reply=reply_text
            st.session_state.odd_total=odd_total; st.session_state.odd_cost=odd_cost
            st.session_state.odd_nitem=len(odd_reply); st.session_state.odd_log=odd_log

        if st.session_state.odd_ready:
            render_staff_log(st.session_state.odd_log,st.session_state.odd_total,st.session_state.odd_cost)
            st.divider()
            st.subheader("Customer Reply (edit before sending)")
            odd_edited=st.text_area("",st.session_state.odd_reply,height=300,key="odd_reply_out")
            od1,od2=st.columns(2)
            with od1:
                st.download_button("📥 Download TXT",data=odd_edited,
                    file_name=f"odd_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",use_container_width=True)
            with od2:
                if st.button("💾 Save to History",type="primary",key="save_odd",use_container_width=True):
                    ok=save_quote(st.session_state.cust_name,st.session_state.cust_mobile,
                        st.session_state.odd_total,st.session_state.odd_nitem,odd_edited,
                        st.session_state.odd_cost,quote_type="Odd Size")
                    if ok: st.success("✅ Saved!")
                    else:  st.error("❌ Could not save.")
    else:
        st.info("Fill in the sizes above and click '+ Add to Odd Size List'.")

# ============================================================
# TAB 3 — PLYWOOD
# ============================================================
with tab_ply:
    ply_sub1, ply_sub2, ply_sub3 = st.tabs(["📦 Standard Plywood", "✂️ Cut-to-Size", "📏 Thickness Reference"])

    with ply_sub1:
        st.subheader("Plywood Prices (SGD/sheet)")
        st.caption("Select a grade to view prices. Cost = Ying Chuan. Selling = your price to customer.")

        grade_cols = st.columns(len(PLY_GRADES))
        for i, g in enumerate(PLY_GRADES):
            with grade_cols[i]:
                if st.button(g, key=f"gtab_{i}",
                             type="primary" if st.session_state.sel_grade == g else "secondary",
                             use_container_width=True):
                    st.session_state.sel_grade = g; st.rerun()

        st.divider()
        sel = st.session_state.sel_grade
        with st.expander(f"📋 {sel} — Price Reference (click to view)", expanded=False):
            if sel in PLY_SELL:
                tbl_rows = []
                for thk in sorted(PLY_SELL[sel].keys()):
                    cost=PLY_COST.get(sel,{}).get(thk,0.0); sell_def=PLY_SELL[sel][thk]
                    profit=round(sell_def-cost,2); margin=round((profit/sell_def*100),1) if sell_def>0 else 0
                    note=PLY_ACTUAL.get(sel,{}).get(thk,""); moq=PLY_MOQ.get(sel,{}).get(thk,1)
                    notes=[]
                    if note: notes.append(note)
                    if moq>1: notes.append(f"MOQ {moq} sheets")
                    tbl_rows.append({"Thickness":f"{thk}mm","YC Cost":f"S${cost}","Sell Price":f"S${sell_def}",
                        "Profit":f"S${profit}","Margin":f"{margin}%","Notes":" · ".join(notes) if notes else "—"})
                render_table(tbl_rows)

        st.divider()
        st.subheader("Add Plywood to Order")
        if "ply_cur_grade" not in st.session_state:
            st.session_state.ply_cur_grade = st.session_state.sel_grade

        pg1, pg2 = st.columns(2)
        with pg1:
            p_grade=st.selectbox("Grade",PLY_GRADES,index=PLY_GRADES.index(st.session_state.ply_cur_grade),key="p_gr_sel")
            st.session_state.ply_cur_grade=p_grade
        with pg2:
            avail_thk=sorted(PLY_SELL.get(p_grade,{}).keys())
            p_thk_key=f"p_thk_{p_grade}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            p_thk=st.selectbox("Thickness (mm)",avail_thk,key=p_thk_key)

        p_sell_def=PLY_SELL.get(p_grade,{}).get(p_thk,0.0)
        p_cost_def=PLY_COST.get(p_grade,{}).get(p_thk,0.0)
        note=PLY_ACTUAL.get(p_grade,{}).get(p_thk,""); moq=PLY_MOQ.get(p_grade,{}).get(p_thk,1)
        if note: st.caption(f"ℹ️ {note}")
        if moq>1: st.caption(f"⚠️ MOQ: minimum {moq} sheets for this item")
        profit_preview=round(p_sell_def-p_cost_def,2)
        margin_preview=round((profit_preview/p_sell_def*100),1) if p_sell_def>0 else 0

        with st.form("ply_add_form",clear_on_submit=True):
            fa1,fa2,fa3,fa4=st.columns([2,1,1,1])
            with fa1:
                p_sell_key=f"ply_sell_{p_grade}_{p_thk}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
                p_sell_f=st.number_input("Selling Price (S$/sheet)",min_value=0.0,value=float(p_sell_def),step=0.5,format="%.2f",key=p_sell_key)
            with fa2: p_qty_f=st.number_input("Qty (sheets)",min_value=1,value=1,step=1,key="ply_qty_form")
            with fa3: st.markdown(f"<br><small>Default profit:<br>S${profit_preview}/sheet ({margin_preview}%)</small>",unsafe_allow_html=True)
            with fa4: st.markdown("<br>",unsafe_allow_html=True); add_ply=st.form_submit_button("+ Add Plywood",type="primary",use_container_width=True)
            st.caption("Press Enter or click '+ Add Plywood'.")

        if p_sell_def==0.0: st.warning("⚠️ Selling price is S$0.00 — check price table.")
        if add_ply:
            actual_qty=max(p_qty_f,moq); moq_flag=actual_qty>p_qty_f
            line_total=round(p_sell_f*actual_qty,2)
            st.session_state.ply_items.append({
                "grade":p_grade,"thk":p_thk,"sell":p_sell_f,"cost":p_cost_def,
                "qty":p_qty_f,"actual_qty":actual_qty,"moq_flag":moq_flag,
                "line_total":line_total,"profit_ps":round(p_sell_f-p_cost_def,2)
            })
            st.session_state.ply_ready=False; st.rerun()

        if st.session_state.ply_items:
            st.divider()
            st.markdown("**Items in Order**")
            for i,item in enumerate(st.session_state.ply_items):
                col_a,col_b,col_c,col_d=st.columns([3,3,1,1])
                with col_a:
                    moq_badge=" ⚠️ MOQ" if item["moq_flag"] else ""
                    st.markdown(f"**{item['grade']}** &nbsp; {item['thk']}mm{moq_badge}",unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"S\\${item['sell']}/sheet &nbsp;×&nbsp; {item['actual_qty']} sheets &nbsp;=&nbsp; **S\\${item['line_total']:,.2f}**",unsafe_allow_html=True)
                with col_c: st.caption(f"Profit: S${round(item['profit_ps']*item['actual_qty'],2):,.2f}")
                with col_d:
                    if st.button("🗑️",key=f"dply_{i}"):
                        st.session_state.ply_items.pop(i); st.session_state.ply_ready=False; st.rerun()

            st.divider()
            ply_grand=round(sum(x["line_total"] for x in st.session_state.ply_items),2)
            ply_cost_total=round(sum(x["cost"]*x["actual_qty"] for x in st.session_state.ply_items),2)
            ply_profit=round(ply_grand-ply_cost_total,2)
            ply_margin=round((ply_profit/ply_grand*100),1) if ply_grand>0 else 0

            pm1,pm2,pm3,pm4=st.columns(4)
            with pm1: st.metric("Items Quoted",len(st.session_state.ply_items))
            with pm2: st.metric("Plywood Total",f"S${ply_grand:,.2f}")
            with pm3: st.metric("Profit",f"S${ply_profit:,.2f}")
            with pm4: st.metric("Margin",f"{ply_margin}%")

            pg1,pg2=st.columns([2,1])
            with pg1: gen_ply=st.button("GENERATE PLYWOOD QUOTE",type="primary",use_container_width=True)
            with pg2:
                if st.button("Clear Plywood",use_container_width=True):
                    st.session_state.ply_items=[]; st.session_state.ply_ready=False; st.rerun()

            if gen_ply:
                ply_log=[]; ply_reply=[]
                for item in st.session_state.ply_items:
                    profit_total=round(item["profit_ps"]*item["actual_qty"],2)
                    margin_pct=round((item["profit_ps"]/item["sell"]*100),1) if item["sell"]>0 else 0
                    moq_note_txt=f"\n(MOQ {item['actual_qty']} sheets applied)" if item["moq_flag"] else ""
                    ply_log.append({
                        "heading":f"{item['grade']} {item['thk']}mm",
                        "rows":{"Cost (YC)":f"S${item['cost']}/sheet","Selling":f"S${item['sell']}/sheet",
                            "Qty":f"{item['actual_qty']} sheets","Line total":f"S${item['line_total']:,.2f}"},
                        "profit_line":f"S${profit_total:,.2f}","margin_pct":f"{margin_pct}%","small_qty":False,
                        "moq_flag":item["moq_flag"],"moq_note":f"min {item['actual_qty']} sheets (requested {item['qty']})"
                    })
                    cl=f"{item['grade']} plywood {item['thk']}mm @ S${item['sell']}/sheet x {item['actual_qty']} = S${item['line_total']:,.2f}{moq_note_txt}"
                    if "Fire Retardant" in item['grade']:
                        cl+="\n  * Plywood may/will be wet & may/will have some powder when dried."
                    ply_reply.append(cl)

                has_fr=any("Fire Retardant" in x["grade"] for x in st.session_state.ply_items)
                fr_note="\n  * Plywood may/will be wet & may/will have some powder when dried." if has_fr else ""
                reply_txt=build_reply(ply_reply,ply_grand,is_timber=False,extra_note=fr_note)
                st.session_state.ply_ready=True; st.session_state.ply_reply=reply_txt
                st.session_state.ply_total=ply_grand; st.session_state.ply_cost=ply_cost_total
                st.session_state.ply_nitem=len(ply_reply); st.session_state.ply_log=ply_log

            if st.session_state.ply_ready:
                render_staff_log(st.session_state.ply_log,st.session_state.ply_total,st.session_state.ply_cost)
                st.divider()
                st.subheader("Customer Reply (edit before sending)")
                ply_edited=st.text_area("",st.session_state.ply_reply,height=300,key="ply_reply_out")
                pl1,pl2=st.columns(2)
                with pl1:
                    st.download_button("📥 Download TXT",data=ply_edited,
                        file_name=f"ply_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",use_container_width=True)
                with pl2:
                    if st.button("💾 Save to History",type="primary",key="save_ply",use_container_width=True):
                        ok=save_quote(st.session_state.cust_name,st.session_state.cust_mobile,
                            st.session_state.ply_total,st.session_state.ply_nitem,ply_edited,st.session_state.ply_cost)
                        if ok: st.success("✅ Saved!")
                        else:  st.error("❌ Could not save.")
        else:
            st.info("Select a grade above, then add items to the order.")

    with ply_sub2:
        st.subheader("✂️ Cut-to-Size Plywood Calculator")
        st.caption("Full sheet size: 4' x 8' (1220mm x 2440mm)")

        if st.button("🔄 Refresh / New Customer",use_container_width=False):
            for k in ["cut_ready","cut_reply","cut_total","cut_cost"]:
                st.session_state[k]=False if k=="cut_ready" else (0.0 if k in ["cut_total","cut_cost"] else "")
            st.rerun()

        cut_col1,cut_col2=st.columns(2)
        with cut_col1: c_grade=st.selectbox("Plywood Grade",PLY_GRADES,key="cut_grade_sel")
        with cut_col2:
            c_thk_opts=sorted(PLY_SELL.get(c_grade,{}).keys())
            c_thk_key=f"cut_thk_{c_grade}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            c_thk=st.selectbox("Thickness (mm)",c_thk_opts,key=c_thk_key)

        c_sell_def=PLY_SELL.get(c_grade,{}).get(c_thk,0.0)
        c_sell_key=f"cut_sell_{c_grade}_{c_thk}".replace(" ","_").replace("/","_").replace("(","").replace(")","")

        with st.form("cut_form",clear_on_submit=False):
            c_sell=st.number_input("Selling Price per full sheet (S$)",min_value=0.0,value=float(c_sell_def),step=0.5,format="%.2f",key=c_sell_key)
            st.markdown("**Cut dimensions required**")
            cd1,cd2,cd3=st.columns(3)
            with cd1: c_w  =st.number_input("Cut Width (mm)", min_value=None,value=None,placeholder="e.g. 800",step=10.0,key="cut_w")
            with cd2: c_l  =st.number_input("Cut Length (mm)",min_value=None,value=None,placeholder="e.g. 800",step=10.0,key="cut_l")
            with cd3: c_qty=st.number_input("Qty (cut pcs)",  min_value=1,   value=10,  step=1,               key="cut_qty")
            calc_cut=st.form_submit_button("Calculate",use_container_width=True,type="primary")

        if calc_cut and c_w and c_l:
            # FIX 3: validate cut dimensions against sheet size
            cut_errors=[]
            if c_w>=FULL_W: cut_errors.append(f"Cut width {int(c_w)}mm must be less than sheet width {FULL_W}mm")
            if c_l>=FULL_L: cut_errors.append(f"Cut length {int(c_l)}mm must be less than sheet length {FULL_L}mm")
            if cut_errors:
                for err in cut_errors: st.error(f"❌ {err}")
            else:
                pcs_w=math.floor(FULL_W/c_w); pcs_l=math.floor(FULL_L/c_l)
                pps=max(pcs_w*pcs_l,1); sheets=math.ceil(c_qty/pps)
                price_pc=round(c_sell/pps,2)
                cuts_per_sheet=(pcs_w-1)+(pcs_l-1) if pps>1 else 0
                total_cuts=cuts_per_sheet*sheets
                total_cut_fee=round(total_cuts*2.50,2)
                cut_fee_per_pc=round(total_cut_fee/c_qty,2) if c_qty>0 else 0
                ply_cost_only=round(price_pc*c_qty,2)
                total=round(ply_cost_only+total_cut_fee,2)
                total_per_pc=round(price_pc+cut_fee_per_pc,2)
                cost=PLY_COST.get(c_grade,{}).get(c_thk,0.0); cost_pc=round(cost/pps,2)
                profit_pc=round(total_per_pc-cost_pc,2); profit_total=round(profit_pc*c_qty,2)
                margin=round((profit_pc/total_per_pc*100),1) if total_per_pc>0 else 0

                cr1,cr2,cr3,cr4=st.columns(4)
                with cr1: st.metric("Pcs per sheet",pps)
                with cr2: st.metric("Sheets needed",sheets)
                with cr3: st.metric("Ply price/pc",f"S${price_pc}")
                with cr4: st.metric("Total (incl. cutting)",f"S${total:,.2f}")
                pm1,pm2,pm3,pm4=st.columns(4)
                with pm1: st.metric("Total cuts needed",total_cuts)
                with pm2: st.metric("Cutting fee",f"S${total_cut_fee:,.2f}")
                with pm3: st.metric("Total per pc",f"S${total_per_pc}")
                with pm4: st.metric("Margin",f"{margin}%")

                cut_log=[{"heading":f"{c_grade} {c_thk}mm — Cut {int(c_w)}mm x {int(c_l)}mm",
                    "rows":{"Full sheet":f"{FULL_W}x{FULL_L}mm",
                        "Pricing per full sheet":f"S${c_sell}","Pcs per sheet":f"{pps} ({pcs_w}w x {pcs_l}l)",
                        "Sheets needed":str(sheets),"Ply price per pc":f"S${price_pc}",
                        "Cuts per sheet":str(cuts_per_sheet),"Total cuts":str(total_cuts),
                        "Cutting fee (S$2.50/cut)":f"S${total_cut_fee:,.2f}","Cutting fee per pc":f"S${cut_fee_per_pc}",
                        "Total per pc (ply+cut)":f"S${total_per_pc}","Qty":f"{c_qty} pcs","Grand total":f"S${total:,.2f}"},
                    "profit_line":f"S${profit_total:,.2f}","margin_pct":f"{margin}%","small_qty":False}]
                render_staff_log(cut_log,total,round(cost_pc*c_qty,2))

                cut_reply_text=(
                    f"{c_grade} plywood {c_thk}mm\nCut size {int(c_w)}mm x {int(c_l)}mm\n"
                    f"Plywood: S${price_pc}/pc x {c_qty} = S${ply_cost_only:,.2f}\n"
                    f"Cutting fee ({total_cuts} cuts @ S$2.50/cut) = S${total_cut_fee:,.2f}\n"
                    f"Total per pc: S${total_per_pc}\n\nTotal : S${total:,.2f}"
                    f"\nCutting Tolerance: +-0.5~1mm\nDelivery / Self Collection:"
                    f"\n30 Kranji Loop (Blk A) #04-05\nTimMac @ Kranji S739570"
                )
                st.session_state.cut_ready=True; st.session_state.cut_reply=cut_reply_text
                st.session_state.cut_total=total; st.session_state.cut_cost=round(cost_pc*c_qty,2)

        if st.session_state.cut_ready:
            st.divider()
            cut_edited=st.text_area("Customer Reply",st.session_state.cut_reply,height=260,key="cut_reply_area")
            cx1,cx2=st.columns(2)
            with cx1:
                st.download_button("📥 Download TXT",data=cut_edited,
                    file_name=f"cut_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",use_container_width=True)
            with cx2:
                if st.button("💾 Save to History",type="primary",key="save_cut",use_container_width=True):
                    ok=save_quote(st.session_state.cust_name,st.session_state.cust_mobile,
                        st.session_state.cut_total,1,cut_edited,st.session_state.cut_cost)
                    if ok: st.success("✅ Saved!")
                    else:  st.error("❌ Could not save.")

    with ply_sub3:
        st.subheader("📏 Plywood Thickness Tolerance Reference")
        render_table([
            {"Grade":"MR China",            "Nominal":"3mm","Actual":"+-1.8mm","Supplier":"Ying Chuan","Notes":"China origin"},
            {"Grade":"BB/CC Furniture",      "Nominal":"3mm","Actual":"+-2.2mm","Supplier":"Ying Chuan","Notes":"T2 grade"},
            {"Grade":"WBP (TA)",             "Nominal":"6mm","Actual":"+-5.5mm","Supplier":"Ying Chuan","Notes":"TA grade"},
            {"Grade":"Marine BS1088",        "Nominal":"9mm","Actual":"+-8.5mm","Supplier":"Ying Chuan","Notes":"BS1088 certified"},
            {"Grade":"Fire Retardant BS476", "Nominal":"3mm","Actual":"+-2.8mm","Supplier":"Ying Chuan","Notes":"BS476 Part 7 Class 1"},
        ])

# ============================================================
# TAB 4 — SUPPLIERS
# ============================================================
with tab_sup:
    st.markdown("""<div class="sup-header">
      <div class="sup-avatar">YC</div>
      <div><div class="sup-name">Ying Chuan Timber Co Pte Ltd</div>
      <div class="sup-sub">Supplier 1 &nbsp;·&nbsp; Plony Industries &nbsp;·&nbsp; Updated May 2026</div></div>
    </div>""", unsafe_allow_html=True)

    sup1, sup2 = st.tabs(["📊 Cost vs Selling Price", "📈 Margin Summary"])
    with sup1:
        grade_sel=st.selectbox("Select Grade",PLY_GRADES,key="sup_grade")
        if grade_sel in PLY_COST:
            rows=[]
            for thk,cost in sorted(PLY_COST[grade_sel].items()):
                sell=PLY_SELL.get(grade_sel,{}).get(thk,0)
                profit=round(sell-cost,2); margin=round((profit/sell*100),1) if sell>0 else 0
                note=PLY_ACTUAL.get(grade_sel,{}).get(thk,"")
                rows.append({"Thickness":f"{thk}mm"+(f" ({note})" if note else ""),
                    "Ying Chuan Cost":f"S${cost}","Your Selling Price":f"S${sell}",
                    "Profit/sheet":f"S${profit}","Margin %":f"{margin}%"})
            render_table(rows)
        st.info("More suppliers can be added once you onboard them.")

    with sup2:
        margin_rows=[]
        for grade in PLY_GRADES:
            if grade not in PLY_SELL: continue
            sells=[PLY_SELL[grade][t] for t in PLY_SELL[grade]]
            costs=[PLY_COST.get(grade,{}).get(t,0) for t in PLY_SELL[grade]]
            avg_sell=round(sum(sells)/len(sells),2) if sells else 0
            avg_cost=round(sum(costs)/len(costs),2) if costs else 0
            avg_profit=round(avg_sell-avg_cost,2)
            avg_margin=round((avg_profit/avg_sell*100),1) if avg_sell>0 else 0
            margin_rows.append({"Grade":grade,"Avg Cost":f"S${avg_cost}","Avg Sell":f"S${avg_sell}",
                "Avg Profit":f"S${avg_profit}","Avg Margin":f"{avg_margin}%"})
        render_table(margin_rows)

# ============================================================
# TAB 5 — HISTORY
# ============================================================
with tab_hist:
    st.markdown("#### 🕘 Quote History")
    st.caption("Search by customer name or mobile.")

    with st.form("hist_search_form",clear_on_submit=False):
        hs1,hs2,hs3=st.columns([4,1,1])
        with hs1:
            search=st.text_input("🔍 Search",value=st.session_state.hist_search_val,
                placeholder="Type customer name or mobile — press Enter or click Search",
                key="hist_search_inp",label_visibility="collapsed")
        with hs2: search_btn =st.form_submit_button("🔍 Search", use_container_width=True,type="primary")
        with hs3: refresh_btn=st.form_submit_button("🔄 Refresh",use_container_width=True)

    if refresh_btn: st.session_state.hist_search_val=""; st.rerun()
    elif search_btn: st.session_state.hist_search_val=search

    with st.spinner("Loading history from cloud..."):
        history=load_history()

    if not history:
        st.info("No quotes saved yet. Generate a quote and click 'Save to History'.")
    else:
        active_search=st.session_state.hist_search_val.strip()
        filtered=[q for q in history
            if active_search.lower() in q.get("customer","").lower()
            or active_search in q.get("mobile","")
        ] if active_search else history

        h1,h2,h3,h4=st.columns(4)
        with h1: st.metric("Total Quotes",     len(history))
        with h2: st.metric("All-time Revenue", f"S${sum(float(q.get('total',0)) for q in history):,.2f}")
        with h3: st.metric("All-time Profit",  f"S${sum(float(q.get('profit',0)) for q in history):,.2f}")
        with h4: st.metric("Unique Customers", len(set(q.get("customer","") for q in history if q.get("customer","—")!="—")))
        st.divider()

        if active_search: st.caption(f"{len(filtered)} quote(s) found for '{active_search}'")
        if not filtered:
            st.info("No quotes match your search.")
        else:
            for i,q in enumerate(filtered):
                name=q.get("customer","—"); mobile=q.get("mobile","—")
                date=q.get("date","");      time=q.get("time","")
                total=float(q.get("total",0)); profit=float(q.get("profit",0)); margin=float(q.get("margin",0))
                text=q.get("text",""); qid=q.get("id",str(i)); qtype=q.get("type","Quote")
                type_icon="📐" if qtype=="Odd Size" else "📄"
                label=f"{type_icon} [{qtype}]  {date} {time}  ·  {name}  ·  {mobile}  ·  SGD {total:,.2f}  ·  Profit SGD {profit:,.2f}  ({margin}%)"
                with st.expander(label):
                    st.text_area("Full quote",value=text,height=300,key=f"qt_{i}")
                    hb1,hb2=st.columns(2)
                    with hb1:
                        st.download_button("📥 Download TXT",data=text,
                            file_name=f"quote_{date}_{name}.txt".replace(" ","_"),
                            mime="text/plain",key=f"dl_{i}",use_container_width=True)
                    with hb2:
                        if st.button("🗑️ Delete",key=f"dh_{i}",use_container_width=True):
                            delete_quote(qid); st.success("Deleted."); st.rerun()

# ============================================================
# TAB 6 — AI PARSER
# ============================================================
with tab_ai:
    st.markdown("#### 🤖 AI Quote Parser")
    st.caption("Paste WhatsApp text, typed lists, or Chinese order notes. Parser reads any format instantly.")

    ai_t1, ai_t2 = st.tabs(["📋 Paste Text / WhatsApp", "⌨️ Shorthand Entry"])

    with ai_t1:
        st.markdown("**Paste any format below** — WhatsApp message, Chinese list, email snippet")
        st.markdown("""<div style="background:#f0faf5;border-left:3px solid #1D9E75;padding:8px 14px;border-radius:6px;font-size:12px;color:#555;margin-bottom:8px">
        <b>Supported formats:</b><br>
        • <code>Chengal 35x80 &nbsp; 2400=36支 &nbsp; 1500=16支</code><br>
        • <code>chengal 1080mm L x 300mm W x 70mm H</code><br>
        • <code>chengal 35x80x2400 &nbsp; 50pcs</code><br>
        • <code>pure keruing 43 93 3.0 20</code> &nbsp;— two-word species supported<br>
        • <code>坡楼 35×80 2.4米 36支</code></div>""", unsafe_allow_html=True)

        paste_text=st.text_area("Paste order here",value=st.session_state.ai_input,height=200,
            placeholder="e.g. Chengal 35x80 / 2400=36支 / 1500=16支",
            key="ai_paste_inp",label_visibility="collapsed")
        p1,p2=st.columns(2)
        with p1:
            parse_btn=st.button("🔍 Parse Order",type="primary",use_container_width=True,key="parse_paste_btn")
        with p2:
            if st.button("🗑️ Clear",use_container_width=True,key="clear_paste_btn"):
                st.session_state.ai_input=""; st.session_state.ai_parsed=[]; st.session_state.ai_ran=False; st.rerun()

        if parse_btn and paste_text.strip():
            st.session_state.ai_input=paste_text
            st.session_state.ai_parsed=parse_smart_text(paste_text)
            st.session_state.ai_ran=True; st.rerun()

    with ai_t2:
        st.markdown("**One item per line:** `Species  Thickness  Width  Length(m)  Qty`")
        st.markdown("""<div style="background:#f0faf5;border-left:3px solid #1D9E75;padding:8px 14px;border-radius:6px;font-size:12px;color:#555;margin-bottom:8px">
        <b>Example:</b><br>
        <code>chengal &nbsp; 35 &nbsp; 80 &nbsp; 2.4 &nbsp; 36</code><br>
        <code>kapur &nbsp;&nbsp;&nbsp; 43 &nbsp; 93 &nbsp; 3.0 &nbsp; 50</code><br>
        <code>pure keruing &nbsp; 43 &nbsp; 93 &nbsp; 3.0 &nbsp; 20</code><br>
        <code>mixed keruing &nbsp; 35 &nbsp; 80 &nbsp; 2.4 &nbsp; 10</code></div>""", unsafe_allow_html=True)

        shorthand_text=st.text_area("Shorthand entry",height=180,
            placeholder="chengal 35 80 2.4 36\npure keruing 43 93 3.0 20",
            key="ai_shorthand_inp",label_visibility="collapsed")
        sh1,sh2=st.columns(2)
        with sh1:
            sh_parse_btn=st.button("🔍 Parse Shorthand",type="primary",use_container_width=True,key="parse_sh_btn")
        with sh2:
            if st.button("🗑️ Clear",use_container_width=True,key="clear_sh_btn"):
                st.session_state.ai_parsed=[]; st.session_state.ai_ran=False; st.rerun()

        if sh_parse_btn and shorthand_text.strip():
            st.session_state.ai_parsed=parse_smart_text(shorthand_text)
            st.session_state.ai_ran=True; st.rerun()

    if st.session_state.ai_ran:
        parsed=st.session_state.ai_parsed
        st.divider()

        if not parsed:
            st.warning("⚠️ Could not read any items. Check format and try again.")
            st.markdown("""**Tips:**
- Species name before the dimensions
- Dimensions separated by x: `35x80` or `35 x 80`
- Length=Qty format: `2400=36` or `2400=36支`
- Shorthand: `chengal 35 80 2.4 36`
- Two-word species: `pure keruing 43 93 3.0 20`""")
        else:
            st.success(f"✅ {len(parsed)} item(s) detected — review before sending to quote tab")
            st.markdown("**Review & Edit (click any field to correct)**")

            edited=[]
            hdr=st.columns([2,1,1,1,1,1])
            for col,label in zip(hdr,["**Species**","**Thk (mm)**","**Wid (mm)**","**Len (m)**","**Qty**","**Price/pc**"]):
                col.markdown(label)

            for i,item in enumerate(parsed):
                rate=species_rate.get(item["species"],3800)
                thk_in=item["thk_mm"]/25.4; wid_in=item["wid_mm"]/25.4; len_ft=item["len_m"]*3.28084
                raw=7200/(thk_in*wid_in*len_ft); pcs_f=max(math.floor(raw),1)
                price_preview=round(rate/pcs_f,2)

                c0,c1,c2,c3,c4,c5=st.columns([2,1,1,1,1,1])
                with c0:
                    sp_e=st.selectbox("",SPECIES,
                        index=SPECIES.index(item["species"]) if item["species"] in SPECIES else 0,
                        key=f"ai_sp_{i}",label_visibility="collapsed")
                with c1: thk_e=st.number_input("",value=float(item["thk_mm"]),step=0.5,format="%.1f",key=f"ai_thk_{i}",label_visibility="collapsed")
                with c2: wid_e=st.number_input("",value=float(item["wid_mm"]),step=0.5,format="%.1f",key=f"ai_wid_{i}",label_visibility="collapsed")
                with c3: len_e=st.number_input("",value=float(item["len_m"]), step=0.1,format="%.2f",key=f"ai_len_{i}",label_visibility="collapsed")
                with c4: qty_e=st.number_input("",value=int(item["qty"]),min_value=1,step=1,key=f"ai_qty_{i}",label_visibility="collapsed")
                with c5: st.markdown(f"<div style='padding-top:8px;font-size:13px;color:#0F6E56;font-weight:600'>S${price_preview}</div>",unsafe_allow_html=True)
                edited.append({"species":sp_e,"thk_mm":thk_e,"wid_mm":wid_e,"len_m":len_e,"qty":qty_e})

            st.divider()
            sub_total=0
            for e in edited:
                r=species_rate.get(e["species"],3800)
                ti=e["thk_mm"]/25.4; wi=e["wid_mm"]/25.4; lf=e["len_m"]*3.28084
                pf=max(math.floor(7200/(ti*wi*lf)),1)
                sub_total+=round(r/pf,2)*e["qty"]
            st.metric("Estimated Total",f"S${round(sub_total,2):,.2f}")

            st.markdown("**Send to:**")
            sb1,sb2,sb3=st.columns([2,2,1])
            with sb1:
                if st.button("📋 → Quote Builder (standard sizes)",type="primary",use_container_width=True,key="ai_to_quote"):
                    added=0
                    for e in edited:
                        try:
                            # FIX 1: 2 args only — no inch_to_mm
                            item_obj=parsed_to_order_item(e,species_rate)
                            st.session_state.order_items.append(item_obj)
                            st.session_state.q_ready=False; added+=1
                        except Exception as ex:
                            st.warning(f"⚠️ Skipped one item: {ex}")
                    if added: st.success(f"✅ {added} item(s) added — go to 📋 Quote Builder tab")
                    st.session_state.ai_parsed=[]; st.session_state.ai_ran=False; st.rerun()

            with sb2:
                if st.button("📐 → Odd Size (exact mm pricing)",use_container_width=True,key="ai_to_odd"):
                    added=0
                    for e in edited:
                        try:
                            item_obj=parsed_to_odd_item(e,species_rate)
                            st.session_state.odd_items.append(item_obj)
                            st.session_state.odd_ready=False; added+=1
                        except Exception as ex:
                            st.warning(f"⚠️ Skipped one item: {ex}")
                    if added: st.success(f"✅ {added} item(s) added — go to 📐 Odd Size tab")
                    st.session_state.ai_parsed=[]; st.session_state.ai_ran=False; st.rerun()

            with sb3:
                if st.button("🗑️ Clear All",use_container_width=True,key="ai_clear_all"):
                    st.session_state.ai_parsed=[]; st.session_state.ai_ran=False; st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Timber AI Assistant V26-AI  ·  Professional Quoting System  ·  Prices in SGD  ·  5 bugs fixed")
