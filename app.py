# ============================================================
# Timber AI Assistant V27 — PART 1 of 3
# CONFIG & DATA
# Paste this FIRST at the top of your app.py in GitHub
# ============================================================

import streamlit as st
import math
import json
import requests
import re
from datetime import datetime

st.set_page_config(layout="wide", page_title="Timber AI Assistant V28", page_icon="🪵")

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

# inch nominal → actual mm (for display only in Quote Builder)
inch_to_mm = {1:20, 2:43, 3:70, 4:93, 5:117, 6:143, 7:168, 8:193, 9:218, 10:243, 12:293}

PLY_GRADES = [
    "MR China", "WBP (TA)", "BB/CC Furniture",
    "Casting Black China", "Casting Black Vietnam",
    "Marine BS1088", "T2 Marine", "Fire Retardant BS476"
]

# ============================================================
# STANDARD SIZES DATABASE — all sizes 6~22 ft
# Format: (width_mm, height_mm, nominal_inch_label)
# pcs/ton calculated live from dimensions; no hardcoded pcs table needed.
# ============================================================
STANDARD_FT  = [6, 8, 10, 12, 14, 16, 18, 20, 22]
ODD_FT       = list(range(1, 23))  # 1~22ft — covers all odd lengths like 5ft, 7ft, 9ft
FT_TO_M      = {
    1:0.3,  2:0.6,  3:0.9,  4:1.2,  5:1.5,  6:1.8,  7:2.1,  8:2.4,  9:2.7,
    10:3.0, 11:3.3, 12:3.6, 13:3.9, 14:4.2, 15:4.5, 16:4.8, 17:5.1,
    18:5.4, 19:5.7, 20:6.0, 21:6.4, 22:6.6,
}
TIMBER_DENSITY_KG_M3 = 706  # calibrated to trade standard: 7200 / (w_inch * h_inch * l_ft)

STANDARD_SIZES = [
    # (width_mm, thickness_mm, display_label, nom_w_inch, nom_h_inch)
    # Display label = planed size (sawn - 5mm each dim), except 1x1 stays 20x20
    # Nominal inches used for 7200 formula — unchanged
    # 1" group
    (25,  25,  '20 x 20mm (1" x 1")',    1,  1),   # QB — keep as 20x20
    # 2" group
    (51,  25,  '45 x 20mm (2" x 1")',    2,  1),   # QB
    (51,  51,  '45 x 45mm (2" x 2")',    2,  2),   # QB
    # 3" group
    (76,  25,  '70 x 20mm (3" x 1")',    3,  1),   # QB
    (76,  51,  '70 x 45mm (3" x 2")',    3,  2),   # QB
    (76,  76,  '70 x 70mm (3" x 3")',    3,  3),   # QB
    # 4" group
    (102, 25,  '95 x 20mm (4" x 1")',    4,  1),   # QB
    (102, 51,  '95 x 45mm (4" x 2")',    4,  2),   # QB
    (102, 76,  '95 x 70mm (4" x 3")',    4,  3),   # QB
    (102, 102, '95 x 95mm (4" x 4")',    4,  4),   # QB
    # 5" group — ODD SIZE only
    (127, 25,  '120 x 20mm (5" x 1")',   None, None),
    (127, 51,  '120 x 45mm (5" x 2")',   None, None),
    (127, 76,  '120 x 70mm (5" x 3")',   None, None),
    (127, 102, '120 x 95mm (5" x 4")',   None, None),
    (127, 127, '120 x 120mm (5" x 5")',  None, None),
    # 6" group
    (152, 25,  '145 x 20mm (6" x 1")',   6,  1),   # QB
    (152, 51,  '145 x 45mm (6" x 2")',   6,  2),   # QB
    (152, 76,  '145 x 70mm (6" x 3")',   6,  3),   # QB
    (152, 102, '145 x 95mm (6" x 4")',   6,  4),   # QB
    (152, 127, '145 x 120mm (6" x 5")',  6,  5),   # QB
    (152, 152, '145 x 145mm (6" x 6")',  6,  6),   # QB
    # 7" group — ODD SIZE only
    (178, 25,  '170 x 20mm (7" x 1")',   None, None),
    (178, 51,  '170 x 45mm (7" x 2")',   None, None),
    (178, 76,  '170 x 70mm (7" x 3")',   None, None),
    (178, 102, '170 x 95mm (7" x 4")',   None, None),
    (178, 152, '170 x 145mm (7" x 6")',  None, None),
    (178, 178, '170 x 170mm (7" x 7")',  None, None),
    # 8" group
    (203, 25,  '195 x 20mm (8" x 1")',   8,  1),   # QB
    (203, 51,  '195 x 45mm (8" x 2")',   8,  2),   # QB
    (203, 76,  '195 x 70mm (8" x 3")',   8,  3),   # QB
    (203, 102, '195 x 95mm (8" x 4")',   8,  4),   # QB
    # 10" group
    (254, 25,  '245 x 20mm (10" x 1")',  10, 1),   # QB
    (254, 51,  '245 x 45mm (10" x 2")',  10, 2),   # QB
    (254, 76,  '245 x 70mm (10" x 3")',  10, 3),   # QB
    # 11" group — ODD SIZE only
    (279, 25,  '270 x 20mm (11" x 1")',  None, None),
    (279, 51,  '270 x 45mm (11" x 2")',  None, None),
    (279, 76,  '270 x 70mm (11" x 3")',  None, None),
    (279, 102, '270 x 95mm (11" x 4")',  None, None),
    (279, 152, '270 x 145mm (11" x 6")', None, None),
    # 12" group
    (305, 25,  '300 x 20mm (12" x 1")',  12, 1),   # QB
    (305, 51,  '300 x 45mm (12" x 2")',  12, 2),   # QB
    (305, 76,  '300 x 70mm (12" x 3")',  12, 3),   # QB
    (305, 102, '300 x 95mm (12" x 4")',  12, 4),   # QB
    (305, 127, '300 x 120mm (12" x 5")', 12, 5),   # QB
    (305, 152, '300 x 145mm (12" x 6")', 12, 6),   # QB
    (305, 203, '300 x 195mm (12" x 8")', 12, 8),   # QB
]

# Trade mm → nominal inch lookup (for odd size 7200 formula)
TRADE_MM_TO_INCH = {
    20:1, 25:1,
    43:2, 45:2, 50:2, 51:2,
    70:3, 75:3, 76:3,
    93:4, 95:4, 100:4, 102:4,
    117:5, 120:5, 125:5, 127:5,
    143:6, 145:6, 150:6, 152:6,
    168:7, 170:7, 175:7, 178:7,
    193:8, 195:8, 200:8, 203:8,
    218:9, 220:9, 225:9, 229:9,
    243:10, 245:10, 250:10, 254:10,
    268:11, 270:11, 275:11, 279:11,
    293:12, 295:12, 300:12, 305:12,
}

def mm_to_nominal_inch(mm):
    """Convert actual mm to nearest nominal trade inch."""
    mm_int = int(round(mm))
    if mm_int in TRADE_MM_TO_INCH:
        return TRADE_MM_TO_INCH[mm_int]
    closest = min(TRADE_MM_TO_INCH.keys(), key=lambda k: abs(k - mm_int))
    return TRADE_MM_TO_INCH[closest]

def m_to_nominal_ft(l_m, ft_list=None):
    """Ceiling to next standard ft — so customer length is always covered.
    0.01 tolerance handles float round-trip errors (e.g. 21ft→6.4008m→21.003ft).
    """
    if ft_list is None:
        ft_list = STANDARD_FT
    ft = l_m * 3.28084
    for f in sorted(ft_list):
        if f >= ft - 0.01:
            return f
    return sorted(ft_list)[-1]

# QB sizes only (exclude 5", 7", 11" odd groups)
QB_SIZES = [s for s in STANDARD_SIZES if s[3] is not None]

# All sizes for Odd Size dropdown (full list)
ODD_SIZES = STANDARD_SIZES

def size_options_for_dropdown():
    return [s[2] for s in QB_SIZES]

def odd_size_options_for_dropdown():
    return [s[2] for s in ODD_SIZES]

def lookup_size(label):
    """Return (width_mm, thickness_mm, nom_w_inch, nom_h_inch)."""
    for entry in STANDARD_SIZES:
        if entry[2] == label:
            return entry[0], entry[1], entry[3], entry[4]
    return None, None, None, None

def suggest_quote_size(cust_w_mm, cust_h_mm):
    """Find nearest size where PLANED dimensions >= customer dimensions."""
    import re
    def planed_dims(lbl):
        m = re.match(r'(\d+)\s*x\s*(\d+)mm', lbl)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    best = None; best_dist = float('inf')
    for entry in ODD_SIZES:
        pw, ph = planed_dims(entry[2])
        if pw >= cust_w_mm and ph >= cust_h_mm:
            dist = (pw - cust_w_mm) + (ph - cust_h_mm)
            if dist < best_dist:
                best_dist = dist; best = entry
    if best is None:
        # fallback: nearest by planed total distance
        for entry in ODD_SIZES:
            pw, ph = planed_dims(entry[2])
            dist = abs(pw - cust_w_mm) + abs(ph - cust_h_mm)
            if dist < best_dist:
                best_dist = dist; best = entry
    return best

def pcs_per_ton(w_mm, h_mm, ft):
    """Calculate pcs/ton from dimensions. Uses volume-weight method."""
    m   = FT_TO_M[ft]
    vol = (w_mm / 1000) * (h_mm / 1000) * m   # m³ per piece
    return max(round(1 / (vol * TIMBER_DENSITY_KG_M3 / 1000)), 1)

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
# SPECIES MAP
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
# SESSION STATE
# ============================================================
_defaults = {
    "order_items": [], "odd_items": [], "ply_items": [],
    "sel_grade":   "MR China",
    "odd_cthk": None, "odd_cwid": None, "odd_clen": None,
    "odd_qthk": None, "odd_qwid": None, "odd_qlen": None,
    "odd_ctu": "mm", "odd_cwu": "mm", "odd_clu": "m",
    "odd_sp":  "Kapur",
    "odd_qsize_label": None,   # selected quote size label from dropdown
    "odd_qft": 8,              # selected quote length ft
    "odd_suggest": None,       # suggested quote size label
    "odd_accept_count": 0,     # incremented on Accept to force fresh widget key
    "odd_qty": 1,
    "cust_name": "", "cust_mobile": "",
    "q_ready":   False, "q_reply":   "", "q_total":   0.0, "q_cost":   0.0, "q_nitem": 0, "q_log":   [],
    "odd_ready": False, "odd_reply": "", "odd_total": 0.0, "odd_cost": 0.0, "odd_nitem":0, "odd_log": [],
    "ply_ready": False, "ply_reply": "", "ply_total": 0.0, "ply_cost": 0.0, "ply_nitem":0, "ply_log": [],
    "hist_search_val": "",
    "rate_reset_key": 0,
    "odd_quickfill": "",
    "odd_qlu_free": "m",
    "qf_fill_key": 0,
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
    <span style="background:#1D9E75;color:white;font-size:13px;padding:2px 8px;border-radius:99px;margin-left:8px;vertical-align:middle">V28</span>
  </div>
  <div class="app-header-sub">Professional Quoting System &nbsp;·&nbsp; Prices in SGD &nbsp;·&nbsp; PLONY Industries</div>
</div>
""", unsafe_allow_html=True)

# Default rate values — used as value= args in number_input widgets
DEFAULT_RATES = {"Kapur": 3800, "Balau": 5500, "Chengal": 6000, "Mixed Keruing": 650, "Pure Keruing": 1000}

# ============================================================
# RATE INPUTS
# ============================================================
st.subheader("Current Rates (SGD/ton)")
rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2, 2, 2, 2, 2, 1])
_rk = st.session_state.rate_reset_key  # changes on reset → forces fresh widget
with rc1: kapur_rate    = st.number_input("Kapur",         min_value=0, value=3800, step=50, key=f"r_kapur_{_rk}")
with rc2: balau_rate    = st.number_input("Balau",         min_value=0, value=5500, step=50, key=f"r_balau_{_rk}")
with rc3: cheng_rate    = st.number_input("Chengal",       min_value=0, value=6000, step=50, key=f"r_cheng_{_rk}")
with rc4: mkeruing_rate = st.number_input("Mixed Keruing", min_value=0, value=650,  step=50, key=f"r_mker_{_rk}")
with rc5: pkeruing_rate = st.number_input("Pure Keruing",  min_value=0, value=1000, step=50, key=f"r_pker_{_rk}")
with rc6:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↩ Reset Rates", use_container_width=True, key="reset_rates_btn"):
        st.session_state.rate_reset_key += 1  # new key suffix → widgets re-instantiate at value= defaults
        st.toast("✅ Rates reset to defaults", icon="↩")
        st.rerun()

species_rate = {
    "Kapur": kapur_rate, "Balau": balau_rate, "Chengal": cheng_rate,
    "Mixed Keruing": mkeruing_rate, "Pure Keruing": pkeruing_rate
}
st.divider()

# ============================================================
# END OF PART 1 — paste Part 2 immediately below this line
# ============================================================
# ============================================================
# Timber AI Assistant V27 — PART 2 of 3
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

def ceil_10cents(x):
    """Round up to nearest 10 cents. e.g. 15.24->15.30, 15.95->16.00"""
    return math.ceil(round(x * 10, 8)) / 10

def calc_from_mm(w_mm, h_mm, ft, rate, nom_w=None, nom_h=None):
    """
    Pricing always uses 7200 / nom_w / nom_h / ft.
    QB: nom_w/nom_h passed directly from STANDARD_SIZES.
    Odd size: nom_w/nom_h derived from mm_to_nominal_inch().
    Price rounded up to nearest 10 cents.
    """
    if nom_w is None or nom_h is None:
        nom_w = mm_to_nominal_inch(w_mm)
        nom_h = mm_to_nominal_inch(h_mm)
    raw_pcs = 7200 / nom_w / nom_h / ft
    pcs     = max(math.floor(raw_pcs), 1)
    price   = ceil_10cents(rate / pcs)
    return round(raw_pcs, 3), pcs, price

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
def validate_odd_inputs(cthk_mm=None, cwid_mm=None, clen_val=None, clu=None,
                         qthk_mm=None, qwid_mm=None, qlen_m=None, qlu=None):
    """Validate Odd Size inputs. Returns list of error strings (empty = all OK)."""
    errors = []
    # Customer dims
    for val, label in [(cthk_mm, "Customer thickness"), (cwid_mm, "Customer width")]:
        if val is not None:
            if val < 20:  errors.append(f"⚠️ {label} {val:.0f}mm is too small (min 20mm)")
            if val > 500: errors.append(f"⚠️ {label} {val:.0f}mm is too large (max 500mm)")
    if clen_val is not None and clu is not None:
        if clu == "m":
            if clen_val < 0.3: errors.append(f"⚠️ Customer length {clen_val}m is too short (min 0.3m)")
            if clen_val > 6.6: errors.append(f"⚠️ Customer length {clen_val}m is too long (max 6.6m = 22ft) — did you mean {clen_val}ft ({round(clen_val*0.3048,1)}m)?")
        elif clu == "ft":
            if clen_val < 1:  errors.append(f"⚠️ Customer length {clen_val}ft is too short (min 1ft)")
            if clen_val > 22: errors.append(f"⚠️ Customer length {clen_val}ft is too long (max 22ft)")
    # Quote dims (free type only)
    for val, label in [(qthk_mm, "Quote thickness"), (qwid_mm, "Quote width")]:
        if val is not None:
            if val < 20:  errors.append(f"⚠️ {label} {val:.0f}mm is too small (min 20mm)")
            if val > 500: errors.append(f"⚠️ {label} {val:.0f}mm is too large (max 500mm)")
    if qlen_m is not None and qlu is not None:
        if qlu == "m":
            if qlen_m < 0.3: errors.append(f"⚠️ Quote length {qlen_m}m is too short (min 0.3m)")
            if qlen_m > 6.6: errors.append(f"⚠️ Quote length {qlen_m}m is too long (max 6.6m = 22ft) — did you mean {qlen_m}ft ({round(qlen_m*0.3048,1)}m)?")
        elif qlu == "ft":
            if qlen_m < 1:  errors.append(f"⚠️ Quote length {qlen_m}ft is too short (min 1ft)")
            if qlen_m > 22: errors.append(f"⚠️ Quote length {qlen_m}ft is too long (max 22ft)")
    return errors

def parse_dimension_string(raw):
    """Parse a free-text dimension string into (thk_mm, wid_mm, len_mm) or None.

    Supported formats (all case-insensitive, mm assumed):
      200x400x1600          200×400×1600       200 400 1600
      T200 W400 L1600       L1600 W400 T200    200T x 400W x 1600L
      200T x 400 x 1600mmL  T200mm W400 L1600mm
    Returns dict with keys 't', 'w', 'l' (all floats in mm), or None on failure.
    """
    import re
    s = raw.strip().upper()
    s = s.replace("MM", "").replace("×", "x")

    labeled = {}
    # Match prefix labels: T200, W400, L1600
    for label, key in [("T", "t"), ("W", "w"), ("L", "l")]:
        m = re.search(rf'\b{label}(\d+(?:\.\d+)?)', s)
        if m:
            labeled[key] = float(m.group(1))

    # Match suffix labels: 200T, 400W, 1600L
    for label, key in [("T", "t"), ("W", "w"), ("L", "l")]:
        if key not in labeled:
            m = re.search(rf'(\d+(?:\.\d+)?){label}\b', s)
            if m:
                labeled[key] = float(m.group(1))

    if len(labeled) == 3:
        return labeled

    # No labels — extract all numbers and sort: smallest=T, middle=W, largest=L
    nums = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', s)]
    if len(nums) == 3:
        t, w, l = sorted(nums)
        return {"t": t, "w": w, "l": l}
    if len(nums) == 2:
        t, w = sorted(nums)
        return {"t": t, "w": w, "l": None}

    return None


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
    return bool(re.match(r'^[a-zA-Z\u4e00-\u9fff]+$', s))

def normalize_to_mm(value, unit):
    u = (unit or "").lower().strip()
    if u in ["mm","毫米",""]:   return float(value)
    if u in ["cm","厘米"]:       return float(value) * 10
    if u in ["m","米"]:          return float(value) * 1000
    if u in ["ft","feet","'"]:  return float(value) * 304.8
    if u in ["in","inch",'"']: return float(value) * 25.4
    return float(value)

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

        two_pat = r"^[^=:\d]*(\d+\.?\d*)\s*(mm|cm)?\s*[xX×]\s*(\d+\.?\d*)\s*(mm|cm)?[^=:\d]*$"
        two_m   = re.match(two_pat, line)
        if two_m:
            v1 = normalize_to_mm(two_m.group(1), two_m.group(2) or "mm")
            v2 = normalize_to_mm(two_m.group(3), two_m.group(4) or "mm")
            cur_thk = min(v1, v2); cur_wid = max(v1, v2)
            continue

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

        ch_m = re.search(r"(\d+\.?\d*)[×xX](\d+\.?\d*)\s+(\d+\.?\d*)米\s*(\d+)支", line)
        if ch_m:
            sp_use = detect_species(line) or cur_sp or "Kapur"
            t = float(ch_m.group(1)); w = float(ch_m.group(2))
            lm = float(ch_m.group(3)); qty = int(ch_m.group(4))
            results.append({"species": sp_use, "thk_mm": min(t, w), "wid_mm": max(t, w), "len_m": lm, "qty": qty})
            cur_thk = min(t, w); cur_wid = max(t, w)
            continue

        qty_only = extract_qty(line)
        if qty_only and results and results[-1].get("qty") == 1:
            results[-1]["qty"] = qty_only

    return results

def parsed_to_order_item(p, species_rate_map):
    thk = p["thk_mm"]; wid = p["wid_mm"]; length_m = p["len_m"]; qty = p["qty"]; sp = p["species"]
    if thk <= 0 or wid <= 0 or length_m <= 0:
        raise ValueError(f"Invalid dimension: thk={thk}, wid={wid}, len={length_m}")
    len_ft = round(length_m * 3.28084)
    rate   = species_rate_map.get(sp, 3800)
    # snap to nearest standard ft
    snapped_ft = min(STANDARD_FT, key=lambda f: abs(f - len_ft))
    raw, pcs, price = calc_from_mm(wid, thk, snapped_ft, rate)
    size_text = f"{thk}mm x {wid}mm x {snapped_ft}ft"
    return {
        "species": sp, "size": size_text, "w_mm": wid, "h_mm": thk, "ft": snapped_ft,
        "price": price, "qty": qty, "line_total": round(price * qty, 2),
        "rate": rate, "pcs_per_ton": raw, "small_qty": qty < SMALL_QTY
    }

def parsed_to_odd_item(p, species_rate_map):
    thk = p["thk_mm"]; wid = p["wid_mm"]; length_m = p["len_m"]; qty = p["qty"]; sp = p["species"]
    if thk <= 0 or wid <= 0 or length_m <= 0:
        raise ValueError(f"Invalid dimension: thk={thk}, wid={wid}, len={length_m}")
    rate      = species_rate_map.get(sp, 3800)
    ft        = m_to_nominal_ft(length_m)
    raw, pcs_floor, price = calc_from_mm(wid, thk, ft, rate)
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
# Timber AI Assistant V27 — PART 3 of 3
# UI TABS: Quote Builder, Odd Size, Plywood, Suppliers, History
# Paste this THIRD, immediately after Part 2
# AI Parser and Plywood Cut-to-Size removed — built as separate apps
# ============================================================

tab_quote, tab_odd, tab_ply, tab_sup, tab_hist = st.tabs([
    "📋 Quote Builder", "📐 Odd Size", "🪵 Plywood",
    "🏭 Suppliers", "🕘 History"
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
    st.caption("Select species, size and length from dropdowns. Rates above update price automatically.")

    size_labels = size_options_for_dropdown()
    ft_labels   = [f"{ft} ft  ({FT_TO_M[ft]} m)" for ft in STANDARD_FT]

    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 1, 1])
    with fc1: f_sp       = st.selectbox("Species", SPECIES, key="f_sp")
    with fc2: f_size     = st.selectbox("Size (mm)", size_labels, key="f_size")
    with fc3: f_ft_label = st.selectbox("Length", ft_labels, key="f_ft")
    with fc4: f_qty      = st.number_input("Qty (pcs)", min_value=1, value=1, step=1, key="f_qty")
    with fc5:
        st.markdown("<br>", unsafe_allow_html=True)
        add_btn = st.button("+ Add", type="primary", use_container_width=True, key="qb_add_btn")

    if add_btn:
        f_qty_int  = max(int(st.session_state.get("f_qty", 1)), 1)
        ft_val     = int(st.session_state.get("f_ft", ft_labels[0]).split(" ")[0])
        f_size_val = st.session_state.get("f_size", size_labels[0])
        f_sp_val   = st.session_state.get("f_sp", SPECIES[0])
        w_mm, h_mm, nom_w, nom_h = lookup_size(f_size_val)
        rate       = species_rate[f_sp_val]
        raw, pcs, price = calc_from_mm(w_mm, h_mm, ft_val, rate, nom_w, nom_h)
        size_text  = f"{f_size_val} x {ft_val}ft"
        st.session_state.order_items.append({
            "species": f_sp_val, "size": size_text, "w_mm": w_mm, "h_mm": h_mm,
            "nom_w": nom_w, "nom_h": nom_h, "ft": ft_val,
            "price": price, "qty": f_qty_int, "line_total": round(price * f_qty_int, 2),
            "rate": rate, "pcs_per_ton": raw, "small_qty": f_qty_int < SMALL_QTY
        })
        st.session_state.q_ready = False
        st.rerun()

    if st.session_state.order_items:
        n_items = len(st.session_state.order_items)
        st.markdown(
            f'<div style="font-size:13px;color:var(--color-text-secondary);margin-bottom:6px">'
            f'Items in order: <span style="background:#1D9E75;color:white;font-size:12px;'
            f'padding:2px 8px;border-radius:99px;font-weight:600">{n_items}</span></div>',
            unsafe_allow_html=True
        )
        # Build per-species rate sets to detect mixed rates within same species
        species_rates_in_order = {}
        for item in st.session_state.order_items:
            sp = item["species"]
            if sp not in species_rates_in_order:
                species_rates_in_order[sp] = set()
            species_rates_in_order[sp].add(item["rate"])

        for i, item in enumerate(st.session_state.order_items):
            locked_rate  = item["rate"]
            mixed_rates  = len(species_rates_in_order[item["species"]]) > 1
            _, _, locked_price = calc_from_mm(
                item["w_mm"], item["h_mm"], item["ft"], locked_rate,
                item.get("nom_w"), item.get("nom_h")
            )
            locked_total = round(locked_price * item["qty"], 2)

            if mixed_rates:
                st.markdown(
                    f'<div style="background:#FAEEDA;border:0.5px solid #FAC775;'
                    f'border-radius:var(--border-radius-md);padding:10px 14px;margin-bottom:6px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center">'
                    f'<div><span style="font-weight:500;font-size:14px;color:#412402">'
                    f'{item["species"]} &nbsp;{item["size"]}</span>'
                    f'<span style="display:inline-block;font-size:11px;padding:1px 8px;border-radius:99px;'
                    f'background:#FAC775;color:#412402;margin-left:8px">@S${locked_rate:,}/ton</span></div>'
                    f'<div style="display:flex;align-items:center;gap:10px;flex-shrink:0;margin-left:16px">'
                    f'<span style="font-size:13px;color:#633806;white-space:nowrap">'
                    f'S${locked_price}/pc × {item["qty"]} = S${locked_total:,.2f}</span></div></div>'
                    f'<div style="font-size:11px;color:#854F0B;margin-top:4px">'
                    f'⚠️ This {item["species"]} item uses a different rate from others in this quote</div></div>',
                    unsafe_allow_html=True
                )
                col_c2, _ = st.columns([1, 11])
                with col_c2:
                    if st.button("🗑️", key=f"dt_{i}"):
                        st.session_state.order_items.pop(i)
                        st.session_state.q_ready = False
                        st.rerun()
            else:
                st.markdown(
                    f'<div style="border:0.5px solid var(--color-border-tertiary);'
                    f'border-radius:var(--border-radius-md);padding:10px 14px;margin-bottom:6px;'
                    f'background:var(--color-background-primary);display:flex;justify-content:space-between;align-items:center">'
                    f'<div><span style="font-weight:500;font-size:14px;color:var(--color-text-primary)">'
                    f'{item["species"]} &nbsp;{item["size"]}</span>'
                    f'<span style="display:inline-block;font-size:11px;padding:1px 8px;border-radius:99px;'
                    f'background:var(--color-background-secondary);color:var(--color-text-secondary);'
                    f'border:0.5px solid var(--color-border-tertiary);margin-left:8px">@S${locked_rate:,}/ton</span></div>'
                    f'<span style="font-size:13px;color:var(--color-text-secondary);white-space:nowrap">'
                    f'S${locked_price}/pc × {item["qty"]} = S${locked_total:,.2f}</span></div>',
                    unsafe_allow_html=True
                )
                col_c2, _ = st.columns([1, 11])
                with col_c2:
                    if st.button("🗑️", key=f"dt_{i}"):
                        st.session_state.order_items.pop(i)
                        st.session_state.q_ready = False
                        st.rerun()

        st.divider()
        cg1, cg2, cg3 = st.columns([2, 1, 1])
        with cg1: gen_quote = st.button("GENERATE QUOTE", type="primary", use_container_width=True)
        with cg2:
            if st.button("🗑️ Clear List", use_container_width=True):
                st.session_state.order_items = []
                st.session_state.q_ready = False
                st.rerun()
        with cg3:
            if st.button("RESET ALL", use_container_width=True): reset_all()

        if gen_quote:
            log_items = []; customer_reply = []; grand_total = 0; cost_total = 0
            for item in st.session_state.order_items:
                locked_rate = item["rate"]
                locked_raw, _, locked_price = calc_from_mm(
                    item["w_mm"], item["h_mm"], item["ft"], locked_rate,
                    item.get("nom_w"), item.get("nom_h")
                )
                gt = round(locked_price * item["qty"], 2)
                grand_total += gt
                cost_est = round(gt * 0.85, 2); cost_total += cost_est
                profit = round(gt - cost_est, 2)
                margin_pct = round((profit / gt * 100), 1) if gt > 0 else 0
                log_items.append({
                    "heading": f"{item['species']} timber · {item['size']}",
                    "rows": {
                        "Rate":            f"S${locked_rate:,}/ton",
                        "Pieces per ton":  str(round(locked_raw, 2)),
                        "Price per piece": f"S${locked_price}",
                        "Qty":             f"{item['qty']} pcs",
                        "Line total":      f"S${gt:,.2f}",
                    },
                    "profit_line": f"S${profit:,.2f}", "margin_pct": f"{margin_pct}%",
                    "small_qty": item["small_qty"]
                })
                customer_reply.append(
                    f"{item['species']} timber\n{item['size']} @ S${locked_price}/pcs x {item['qty']} = S${gt:,.2f}"
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
            a1, a2, a3, a4 = st.columns(4)
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
            with a4:
                if st.button("🗑️ Clear Quote", use_container_width=True, key="clear_reply_q"):
                    st.session_state.order_items = []
                    st.session_state.q_ready = False
                    st.rerun()
    else:
        st.info("Add items above to build your order list.")
        if st.button("RESET ALL", use_container_width=True): reset_all()

# ============================================================
# TAB 2 — ODD SIZE
# ============================================================
with tab_odd:
    st.subheader("📐 Odd Size Timber")
    st.caption("Enter customer requested size (free type). System suggests nearest quote size from dropdown.")

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

    # ── Quick Fill parser ─────────────────────────────────────
    with st.expander("⚡ Quick Fill — paste customer dimensions", expanded=False):
        st.caption("Accepts: 200×400×1600 · T200 W400 L1600 · 200T x 400W x 1600mmL · 200 400 1600 (any order/combo)")
        qf_col1, qf_col2 = st.columns([4, 1])
        with qf_col1:
            st.text_input("Paste dimensions",
                placeholder="e.g.  200×400×1600  or  T200 W400 L1600  or  200T x 400 x 1600mmL",
                label_visibility="collapsed", key="odd_quickfill_inp")
        with qf_col2:
            qf_btn = st.button("Auto-fill ↓", use_container_width=True, key="odd_qf_btn")

        # Must read from session_state key — value= is ignored when key= is set in Streamlit
        _qf_val = st.session_state.get("odd_quickfill_inp", "").strip()
        if qf_btn and _qf_val:
            parsed = parse_dimension_string(_qf_val)
            if parsed:
                st.session_state["odd_cthk"] = float(parsed["t"]) if parsed.get("t") is not None else st.session_state.odd_cthk
                st.session_state["odd_cwid"] = float(parsed["w"]) if parsed.get("w") is not None else st.session_state.odd_cwid
                if parsed.get("l") is not None:
                    st.session_state["odd_clen"] = round(float(parsed["l"]) / 1000, 3)
                    st.session_state["odd_clu"]  = "m"
                st.session_state["odd_ctu"] = "mm"
                st.session_state["odd_cwu"] = "mm"
                # Increment key counter → customer size widgets get brand new keys
                # → render fresh at value= args (same pattern as Reset Rates)
                st.session_state["qf_fill_key"] += 1
                st.rerun()
            else:
                st.error("⚠️ Could not parse — try: 200×400×1600 or T200 W400 L1600")

    # ── Customer Requested Size (free type) ──────────────────
    st.markdown("**① Customer Requested Size** — type exactly what customer asked for")
    cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
    _fk = st.session_state.qf_fill_key
    with cc1: st.session_state.odd_cthk = st.number_input("Thickness", min_value=None, value=st.session_state.odd_cthk, placeholder="e.g. 80",  step=0.5, format="%.1f", key=f"odd_cthk_inp_{_fk}")
    with cc2: st.session_state.odd_ctu  = st.selectbox("Unit",  ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_ctu), key="odd_ctu_sel")
    with cc3: st.session_state.odd_cwid = st.number_input("Width",     min_value=None, value=st.session_state.odd_cwid, placeholder="e.g. 125", step=0.5, format="%.1f", key=f"odd_cwid_inp_{_fk}")
    with cc4: st.session_state.odd_cwu  = st.selectbox("Unit ", ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_cwu), key="odd_cwu_sel")
    with cc5: st.session_state.odd_clen = st.number_input("Length",    min_value=None, value=st.session_state.odd_clen, placeholder="e.g. 2.4", step=0.1, format="%.1f", key=f"odd_clen_inp_{_fk}")
    with cc6: st.session_state.odd_clu  = st.selectbox("Unit  ", ["m","ft"], index=["m","ft"].index(st.session_state.odd_clu), key="odd_clu_sel")

    # ── Suggest nearest quote size ────────────────────────────
    cthk_val = st.session_state.odd_cthk
    cwid_val  = st.session_state.odd_cwid

    if cthk_val and cwid_val:
        ctu = st.session_state.odd_ctu; cwu = st.session_state.odd_cwu
        cthk_mm = float(cthk_val) * 25.4 if ctu == "inch" else float(cthk_val)
        cwid_mm  = float(cwid_val)  * 25.4 if cwu == "inch" else float(cwid_val)
        # Sort so smaller = thickness, larger = width — entry order doesn't matter
        cthk_mm, cwid_mm = sorted([cthk_mm, cwid_mm])
        sug = suggest_quote_size(cthk_mm, cwid_mm)

        # Suggest nearest standard ft from customer length
        clen_val = st.session_state.odd_clen
        clu      = st.session_state.odd_clu
        if clen_val:
            clen_m   = float(clen_val) if clu == "m" else float(clen_val) * 0.3048
            sug_ft   = m_to_nominal_ft(clen_m, ODD_FT)
        else:
            sug_ft   = 8  # default

        if sug:
            sug_w, sug_h, sug_lbl, _, _ = sug
            sug_full = f"{sug_lbl} × {sug_ft}ft ({FT_TO_M[sug_ft]}m)"
            st.markdown(
                f'<div style="background:var(--color-background-info);border:0.5px solid var(--color-border-tertiary);'
                f'border-radius:var(--border-radius-md);padding:10px 16px;margin:10px 0">'
                f'<div style="font-size:12px;color:var(--color-text-secondary);margin-bottom:4px">💡 Suggested quote size</div>'
                f'<div style="font-family:var(--font-mono);font-weight:600;font-size:15px;color:var(--color-text-primary)">{sug_full}</div>'
                f'<div style="font-size:11px;color:var(--color-text-secondary);margin-top:3px">'
                f'Planed {sug_w}×{sug_h}mm ≥ customer {int(cthk_mm)}×{int(cwid_mm)}mm &nbsp;·&nbsp; {sug_ft}ft nearest to customer {clen_val}{clu if clen_val else ""}'
                f'</div></div>',
                unsafe_allow_html=True
            )
            if st.button(f"✅ Accept — {sug_full}", key="odd_accept_suggest"):
                st.session_state.odd_qsize_label = sug_lbl
                st.session_state.odd_qft = sug_ft
                st.rerun()

    st.markdown("**② Your Quote Size** — select from dropdown or type freely (used for pricing)")

    odd_all_labels = odd_size_options_for_dropdown()
    ft_labels_odd  = [f"{ft} ft  ({FT_TO_M[ft]} m)" for ft in ODD_FT]

    # Toggle: dropdown vs free type
    if "odd_qmode" not in st.session_state:
        st.session_state.odd_qmode = "dropdown"
    if "odd_qthk_free" not in st.session_state:
        st.session_state.odd_qthk_free = None
    if "odd_qwid_free" not in st.session_state:
        st.session_state.odd_qwid_free = None
    if "odd_qlen_free" not in st.session_state:
        st.session_state.odd_qlen_free = None

    st.markdown("""
    <style>
    div[data-testid="stRadio"] label { font-size:15px !important; font-weight:500 !important; }
    div[data-testid="stRadio"] { display:flex; justify-content:center; margin-bottom:8px; }
    </style>""", unsafe_allow_html=True)
    mode = st.radio("Quote size input mode", ["📋 Dropdown", "✏️ Free Type"], horizontal=True,
                    index=0 if st.session_state.odd_qmode == "dropdown" else 1,
                    key="odd_qmode_radio")
    st.session_state.odd_qmode = "dropdown" if "Dropdown" in mode else "free"

    # Default index for length dropdown
    # selectbox keys drive dropdown values directly via session state

    if st.session_state.odd_qmode == "dropdown":
        qd1, qd2 = st.columns([3, 2])

        _qsize_idx = 0
        if st.session_state.get("odd_qsize_label") in odd_all_labels:
            _qsize_idx = odd_all_labels.index(st.session_state.odd_qsize_label)

        _ft_labels_idx = 0
        _sug_ft_str = f"{st.session_state.odd_qft} ft  ({FT_TO_M.get(st.session_state.odd_qft, 2.4)} m)"
        if _sug_ft_str in ft_labels_odd:
            _ft_labels_idx = ft_labels_odd.index(_sug_ft_str)

        with qd1:
            # No key= — index= fully controls the displayed value
            selected_qsize = st.selectbox(
                "Quote Size (thickness × width)",
                odd_all_labels, index=_qsize_idx
            )
            st.session_state.odd_qsize_label = selected_qsize

        with qd2:
            # No key= — index= fully controls the displayed value
            selected_qft_label = st.selectbox(
                "Quote Length", ft_labels_odd, index=_ft_labels_idx
            )
            selected_qft = int(selected_qft_label.split(" ")[0])
            st.session_state.odd_qft = selected_qft

        # Resolve mm dims from dropdown label — odd size ALWAYS uses actual mm
        qw_mm, qh_mm, _, _ = lookup_size(selected_qsize)
        q_len_m_use  = FT_TO_M[selected_qft]
        quote_size_str = f"{selected_qsize} × {selected_qft}ft"

    else:
        # Free type mode
        st.caption("Type any custom quote size — not limited to standard list")
        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
        with fc1:
            st.session_state.odd_qthk_free = st.number_input(
                "Thickness", min_value=None, value=st.session_state.odd_qthk_free,
                placeholder="e.g. 130", step=0.5, format="%.1f", key="odd_qthk_free_inp")
        with fc2:
            st.caption("mm")
        with fc3:
            st.session_state.odd_qwid_free = st.number_input(
                "Width", min_value=None, value=st.session_state.odd_qwid_free,
                placeholder="e.g. 180", step=0.5, format="%.1f", key="odd_qwid_free_inp")
        with fc4:
            st.caption("mm")
        with fc5:
            st.session_state.odd_qlen_free = st.number_input(
                "Length", min_value=None, value=st.session_state.odd_qlen_free,
                placeholder="e.g. 3.0", step=0.1, format="%.2f", key="odd_qlen_free_inp")
        with fc6:
            st.session_state.odd_qlu_free = st.selectbox(
                "Unit   ", ["m", "ft"],
                index=["m", "ft"].index(st.session_state.odd_qlu_free),
                key="odd_qlu_free_sel")

        qh_mm   = float(st.session_state.odd_qthk_free) if st.session_state.odd_qthk_free else None
        qw_mm   = float(st.session_state.odd_qwid_free) if st.session_state.odd_qwid_free else None
        _qlen_raw = float(st.session_state.odd_qlen_free) if st.session_state.odd_qlen_free else None
        _qlu      = st.session_state.odd_qlu_free
        q_len_m_use = (_qlen_raw * 0.3048 if _qlu == "ft" else _qlen_raw) if _qlen_raw else None
        _qlen_display = f"{_qlen_raw}{_qlu}" if _qlen_raw else None
        selected_qft = None
        selected_qsize = (
            f"{st.session_state.odd_qthk_free}mm × {st.session_state.odd_qwid_free}mm"
            if qh_mm and qw_mm else None
        )
        quote_size_str = (
            f"{st.session_state.odd_qthk_free}mm × {st.session_state.odd_qwid_free}mm × {_qlen_display}"
            if qh_mm and qw_mm and q_len_m_use else None
        )

    # ── Validation ───────────────────────────────────────────
    _cthk_val = st.session_state.odd_cthk; _cwid_val = st.session_state.odd_cwid
    _clen_val = st.session_state.odd_clen; _clu = st.session_state.odd_clu
    _ctu = st.session_state.odd_ctu; _cwu = st.session_state.odd_cwu
    _cthk_mm_v = float(_cthk_val) * 25.4 if (_cthk_val and _ctu == "inch") else (float(_cthk_val) if _cthk_val else None)
    _cwid_mm_v = float(_cwid_val) * 25.4 if (_cwid_val and _cwu == "inch") else (float(_cwid_val) if _cwid_val else None)
    _qlu_v = st.session_state.odd_qlu_free if st.session_state.odd_qmode == "free" else None
    _qlen_raw_v = float(st.session_state.odd_qlen_free) if (st.session_state.odd_qmode == "free" and st.session_state.odd_qlen_free) else None

    _val_errors = validate_odd_inputs(
        cthk_mm=_cthk_mm_v, cwid_mm=_cwid_mm_v,
        clen_val=float(_clen_val) if _clen_val else None, clu=_clu,
        qthk_mm=float(st.session_state.odd_qthk_free) if (st.session_state.odd_qmode == "free" and st.session_state.odd_qthk_free) else None,
        qwid_mm=float(st.session_state.odd_qwid_free) if (st.session_state.odd_qmode == "free" and st.session_state.odd_qwid_free) else None,
        qlen_m=_qlen_raw_v, qlu=_qlu_v,
    )
    if _val_errors:
        for _e in _val_errors:
            st.error(_e)

    # Live price preview
    if qw_mm and qh_mm and q_len_m_use and not _val_errors:
        ft_for_calc = m_to_nominal_ft(q_len_m_use, ODD_FT) if selected_qft is None else selected_qft
        raw_pcs, pcs_fl, price_preview = calc_from_mm(qw_mm, qh_mm, ft_for_calc, odd_rate)
        line_preview = round(price_preview * st.session_state.odd_qty, 2)
        nom_w_disp = mm_to_nominal_inch(qw_mm); nom_h_disp = mm_to_nominal_inch(qh_mm)
        st.caption(
            f"Preview: {quote_size_str}  →  "
            f"7200/{nom_w_disp}/{nom_h_disp}/{ft_for_calc}ft = {round(raw_pcs, 2)} pcs/ton (floor {pcs_fl})  →  "
            f"**S${price_preview}/pc × {st.session_state.odd_qty} = S${line_preview:,.2f}**"
        )

    ob1, ob2 = st.columns(2)
    with ob1:
        cthk = st.session_state.odd_cthk; cwid = st.session_state.odd_cwid; clen = st.session_state.odd_clen
        if st.button("+ Add to Odd Size List", type="primary", use_container_width=True):
            if _val_errors:
                st.error("Fix the errors above before adding.")
            elif cthk and cwid and clen and qw_mm and qh_mm and q_len_m_use:
                ctu = st.session_state.odd_ctu; cwu = st.session_state.odd_cwu; clu = st.session_state.odd_clu
                cust_size = (
                    f'{cthk}" x {cwid}" x {clen}{"ft" if clu=="ft" else "m"}'
                    if ctu == "inch"
                    else f"{cthk}mm x {cwid}mm x {clen}{clu}"
                )
                ft_for_add  = m_to_nominal_ft(q_len_m_use, ODD_FT) if selected_qft is None else selected_qft
                raw2, pcs_fl2, price2 = calc_from_mm(qw_mm, qh_mm, ft_for_add, odd_rate)
                line_tot2   = round(price2 * st.session_state.odd_qty, 2)
                st.session_state.odd_items.append({
                    "species":     st.session_state.odd_sp,
                    "cust_size":   cust_size,
                    "quote_size":  quote_size_str,
                    "price":       price2,
                    "qty":         st.session_state.odd_qty,
                    "line_total":  line_tot2,
                    "rate":        odd_rate,
                    "pcs_per_ton": round(raw2, 4),
                    "pcs_floor":   pcs_fl2,
                    "small_qty":   st.session_state.odd_qty < SMALL_QTY
                })
                st.session_state.odd_ready = False
                st.session_state.odd_qsize_label = None
                st.session_state.odd_qthk_free = None
                st.session_state.odd_qwid_free = None
                st.session_state.odd_qlen_free = None
                st.success(f"Added: {cust_size} → priced as {quote_size_str} @ S${price2}/pc")
                st.rerun()
            else:
                st.error("Please fill in all customer size fields and quote size before adding.")
    with ob2:
        if st.button("Clear Inputs", use_container_width=True):
            for k in ["odd_cthk","odd_cwid","odd_clen","odd_qsize_label","odd_suggest",
                      "odd_qthk_free","odd_qwid_free","odd_qlen_free"]:
                st.session_state[k] = None
            st.session_state.odd_qft = 8
            st.session_state.odd_qlu_free = "m"
            st.session_state.odd_quickfill = ""
            st.session_state.qf_fill_key += 1
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
                        "Price per piece":  f"S${item['price']} (rounded up to nearest 10 cents)",
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
        st.info("Fill in customer size above, accept or pick a quote size, then click '+ Add to Odd Size List'.")

# TAB 3 — PLYWOOD
# ============================================================
with tab_ply:
    ply_sub1, ply_sub2 = st.tabs(["📦 Standard Plywood", "📏 Thickness Reference"])

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

        fa1,fa2,fa3,fa4=st.columns([2,1,1,1])
        with fa1:
            p_sell_key=f"ply_sell_{p_grade}_{p_thk}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            p_sell_f=st.number_input("Selling Price (S$/sheet)",min_value=0.0,value=float(p_sell_def),step=0.5,format="%.2f",key=p_sell_key)
        with fa2: p_qty_f=st.number_input("Qty (sheets)",min_value=1,value=1,step=1,key="ply_qty_inp")
        with fa3: st.markdown(f"<br><small>Default profit:<br>S${profit_preview}/sheet ({margin_preview}%)</small>",unsafe_allow_html=True)
        with fa4: st.markdown("<br>",unsafe_allow_html=True); add_ply=st.button("+ Add Plywood",type="primary",use_container_width=True,key="ply_add_btn")

        if p_sell_def==0.0: st.warning("⚠️ Selling price is S$0.00 — check price table.")
        if add_ply:
            p_qty_f = max(int(st.session_state.get("ply_qty_inp", 1)), 1)
            p_sell_f = st.session_state.get(p_sell_key, p_sell_def)
            p_sell_rounded = ceil_10cents(p_sell_f)
            actual_qty=max(p_qty_f,moq); moq_flag=actual_qty>p_qty_f
            line_total=round(p_sell_rounded*actual_qty,2)
            st.session_state.ply_items.append({
                "grade":p_grade,"thk":p_thk,"sell":p_sell_f,"sell_rounded":p_sell_rounded,"cost":p_cost_def,
                "qty":p_qty_f,"actual_qty":actual_qty,"moq_flag":moq_flag,
                "line_total":line_total,"profit_ps":round(p_sell_rounded-p_cost_def,2)
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
                    cl_price = item.get('sell_rounded', ceil_10cents(item['sell']))
                    cl=f"{item['grade']} plywood {item['thk']}mm @ S${cl_price:.2f}/sheet x {item['actual_qty']} = S${item['line_total']:,.2f}{moq_note_txt}"
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
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Timber AI Assistant V27  · ALVIN  ·  Prices in SGD  ·  30 sizes · 6~22ft · AI & Cut-to-Size moved to separate apps")
