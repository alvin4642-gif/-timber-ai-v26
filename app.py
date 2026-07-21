# ============================================================
# CONFIG & DATA
# ============================================================

import streamlit as st
import math
import json
import requests
import re
from datetime import datetime, timezone, timedelta

# Streamlit Cloud servers run in UTC — Singapore has no daylight saving,
# so a fixed +8 offset is reliable without depending on system tzdata
# (zoneinfo needs a tzdata package that isn't always present in minimal
# cloud containers, so a fixed offset is the safer choice here).
SGT = timezone(timedelta(hours=8))
def now_sgt():
    return datetime.now(SGT)

QUOTE_VALIDITY_DAYS = 7  # how many days a quotation stays valid from date of issue

EXPIRING_SOON_WORKING_DAYS = 3  # flag quotes expiring within this many working days

# Singapore public holidays 2026 (11 gazetted + in-lieu Mondays for the
# 3 that fall on a Sunday). Update this list every year — MOM publishes
# the following year's dates around mid-year.
SG_PUBLIC_HOLIDAYS_2026 = {
    "2026-01-01",  # New Year's Day
    "2026-02-17",  # Chinese New Year Day 1
    "2026-02-18",  # Chinese New Year Day 2
    "2026-03-21",  # Hari Raya Puasa (subject to moon-sighting confirmation)
    "2026-04-03",  # Good Friday
    "2026-05-01",  # Labour Day
    "2026-05-27",  # Hari Raya Haji (subject to moon-sighting confirmation)
    "2026-05-31",  # Vesak Day (falls on a Sunday)
    "2026-06-01",  # Vesak Day (in lieu)
    "2026-08-09",  # National Day (falls on a Sunday)
    "2026-08-10",  # National Day (in lieu)
    "2026-11-08",  # Deepavali (falls on a Sunday)
    "2026-11-09",  # Deepavali (in lieu)
    "2026-12-25",  # Christmas Day
}

def is_working_day(date_obj):
    """True if date_obj (a date, not datetime) is a Mon-Fri that isn't
    an SG public holiday."""
    if date_obj.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    return date_obj.strftime("%Y-%m-%d") not in SG_PUBLIC_HOLIDAYS_2026

def add_working_days(start_date, n):
    """Returns the date that is n working days after start_date,
    skipping weekends and SG public holidays."""
    d = start_date
    counted = 0
    while counted < n:
        d += timedelta(days=1)
        if is_working_day(d):
            counted += 1
    return d

st.set_page_config(layout="wide", page_title="Timber AI Assistant V33", page_icon="🪵")

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
    "Marine BS1088", "T2 Marine", "Fire Retardant BS476", "Birch Plywood"
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

def ft_to_m_display(ft):
    """Return m label for any ft value — integer uses trade lookup, half-ft rounded to 1dp."""
    if ft in FT_TO_M:
        return FT_TO_M[ft]
    return round(ft * 0.3048, 1)
TIMBER_DENSITY_KG_M3 = 706  # calibrated to trade standard: 7200 / (w_inch * h_inch * l_ft)

STANDARD_SIZES = [
    # (sawn_w_mm, sawn_h_mm, display_label, nom_w_inch, nom_h_inch)
    # sawn = nom * 25mm  |  planed = sawn - 5mm
    # Exceptions: 13" sawn=330/planed=325 (override); 14" sawn=350/planed=345 (confirmed)
    # All sizes QB + Odd Size

    # 1" group — sawn 25mm / planed 20mm
    (25,  25,  '20 x 20mm (1" x 1")',    1,  1),

    # 2" group — sawn 50mm / planed 45mm
    (50,  25,  '45 x 20mm (2" x 1")',    2,  1),
    (50,  50,  '45 x 45mm (2" x 2")',    2,  2),

    # 3" group — sawn 75mm / planed 70mm
    (75,  25,  '70 x 20mm (3" x 1")',    3,  1),
    (75,  50,  '70 x 45mm (3" x 2")',    3,  2),
    (75,  75,  '70 x 70mm (3" x 3")',    3,  3),

    # 4" group — sawn 100mm / planed 95mm
    (100, 25,  '95 x 20mm (4" x 1")',    4,  1),
    (100, 50,  '95 x 45mm (4" x 2")',    4,  2),
    (100, 75,  '95 x 70mm (4" x 3")',    4,  3),
    (100, 100, '95 x 95mm (4" x 4")',    4,  4),

    # 5" group — sawn 125mm / planed 120mm
    (125, 25,  '120 x 20mm (5" x 1")',   5,  1),
    (125, 50,  '120 x 45mm (5" x 2")',   5,  2),
    (125, 75,  '120 x 70mm (5" x 3")',   5,  3),
    (125, 100, '120 x 95mm (5" x 4")',   5,  4),
    (125, 125, '120 x 120mm (5" x 5")',  5,  5),

    # 6" group — sawn 150mm / planed 145mm
    (150, 25,  '145 x 20mm (6" x 1")',   6,  1),
    (150, 50,  '145 x 45mm (6" x 2")',   6,  2),
    (150, 75,  '145 x 70mm (6" x 3")',   6,  3),
    (150, 100, '145 x 95mm (6" x 4")',   6,  4),
    (150, 125, '145 x 120mm (6" x 5")',  6,  5),
    (150, 150, '145 x 145mm (6" x 6")',  6,  6),

    # 7" group — sawn 175mm / planed 170mm
    (175, 25,  '170 x 20mm (7" x 1")',   7,  1),
    (175, 50,  '170 x 45mm (7" x 2")',   7,  2),
    (175, 75,  '170 x 70mm (7" x 3")',   7,  3),
    (175, 100, '170 x 95mm (7" x 4")',   7,  4),
    (175, 125, '170 x 120mm (7" x 5")',  7,  5),
    (175, 150, '170 x 145mm (7" x 6")',  7,  6),
    (175, 175, '170 x 170mm (7" x 7")',  7,  7),

    # 8" group — sawn 200mm / planed 195mm
    (200, 25,  '195 x 20mm (8" x 1")',   8,  1),
    (200, 50,  '195 x 45mm (8" x 2")',   8,  2),
    (200, 75,  '195 x 70mm (8" x 3")',   8,  3),
    (200, 100, '195 x 95mm (8" x 4")',   8,  4),
    (200, 125, '195 x 120mm (8" x 5")',  8,  5),
    (200, 150, '195 x 145mm (8" x 6")',  8,  6),
    (200, 175, '195 x 170mm (8" x 7")',  8,  7),
    (200, 200, '195 x 195mm (8" x 8")',  8,  8),

    # 9" group — sawn 225mm / planed 220mm (Alvin confirmed)
    (225, 25,  '220 x 20mm (9" x 1")',   9,  1),
    (225, 50,  '220 x 45mm (9" x 2")',   9,  2),
    (225, 75,  '220 x 70mm (9" x 3")',   9,  3),
    (225, 100, '220 x 95mm (9" x 4")',   9,  4),
    (225, 125, '220 x 120mm (9" x 5")',  9,  5),
    (225, 150, '220 x 145mm (9" x 6")',  9,  6),
    (225, 175, '220 x 170mm (9" x 7")',  9,  7),
    (225, 200, '220 x 195mm (9" x 8")',  9,  8),
    (225, 225, '220 x 220mm (9" x 9")',  9,  9),

    # 10" group — sawn 250mm / planed 245mm
    (250, 25,  '245 x 20mm (10" x 1")',  10, 1),
    (250, 50,  '245 x 45mm (10" x 2")',  10, 2),
    (250, 75,  '245 x 70mm (10" x 3")',  10, 3),
    (250, 100, '245 x 95mm (10" x 4")',  10, 4),
    (250, 125, '245 x 120mm (10" x 5")', 10, 5),
    (250, 150, '245 x 145mm (10" x 6")', 10, 6),
    (250, 175, '245 x 170mm (10" x 7")', 10, 7),
    (250, 200, '245 x 195mm (10" x 8")', 10, 8),
    (250, 225, '245 x 220mm (10" x 9")', 10, 9),
    (250, 250, '245 x 245mm (10" x 10")',10,10),

    # 11" group — sawn 275mm / planed 270mm
    (275, 25,  '270 x 20mm (11" x 1")',  11, 1),
    (275, 50,  '270 x 45mm (11" x 2")',  11, 2),
    (275, 75,  '270 x 70mm (11" x 3")',  11, 3),
    (275, 100, '270 x 95mm (11" x 4")',  11, 4),
    (275, 125, '270 x 120mm (11" x 5")', 11, 5),
    (275, 150, '270 x 145mm (11" x 6")', 11, 6),
    (275, 175, '270 x 170mm (11" x 7")', 11, 7),
    (275, 200, '270 x 195mm (11" x 8")', 11, 8),
    (275, 225, '270 x 220mm (11" x 9")', 11, 9),
    (275, 250, '270 x 245mm (11" x 10")',11,10),
    (275, 275, '270 x 270mm (11" x 11")',11,11),

    # 12" group — sawn 300mm / planed 295mm (Alvin confirmed)
    (300, 25,  '295 x 20mm (12" x 1")',  12, 1),
    (300, 50,  '295 x 45mm (12" x 2")',  12, 2),
    (300, 75,  '295 x 70mm (12" x 3")',  12, 3),
    (300, 100, '295 x 95mm (12" x 4")',  12, 4),
    (300, 125, '295 x 120mm (12" x 5")', 12, 5),
    (300, 150, '295 x 145mm (12" x 6")', 12, 6),
    (300, 175, '295 x 170mm (12" x 7")', 12, 7),
    (300, 200, '295 x 195mm (12" x 8")', 12, 8),
    (300, 225, '295 x 220mm (12" x 9")', 12, 9),
    (300, 250, '295 x 245mm (12" x 10")',12,10),
    (300, 275, '295 x 270mm (12" x 11")',12,11),
    (300, 300, '295 x 295mm (12" x 12")',12,12),

    # 13" group — sawn 330mm / planed 325mm (Alvin override)
    (330, 25,  '325 x 20mm (13" x 1")',  13, 1),
    (330, 50,  '325 x 45mm (13" x 2")',  13, 2),
    (330, 75,  '325 x 70mm (13" x 3")',  13, 3),
    (330, 100, '325 x 95mm (13" x 4")',  13, 4),
    (330, 125, '325 x 120mm (13" x 5")', 13, 5),
    (330, 150, '325 x 145mm (13" x 6")', 13, 6),
    (330, 175, '325 x 170mm (13" x 7")', 13, 7),
    (330, 200, '325 x 195mm (13" x 8")', 13, 8),
    (330, 225, '325 x 220mm (13" x 9")', 13, 9),
    (330, 250, '325 x 245mm (13" x 10")',13,10),
    (330, 275, '325 x 270mm (13" x 11")',13,11),
    (330, 300, '325 x 295mm (13" x 12")',13,12),
    (330, 330, '325 x 325mm (13" x 13")',13,13),

    # 14" group — sawn 350mm / planed 345mm (Alvin confirmed)
    (350, 25,  '345 x 20mm (14" x 1")',  14, 1),
    (350, 50,  '345 x 45mm (14" x 2")',  14, 2),
    (350, 75,  '345 x 70mm (14" x 3")',  14, 3),
    (350, 100, '345 x 95mm (14" x 4")',  14, 4),
    (350, 125, '345 x 120mm (14" x 5")', 14, 5),
    (350, 150, '345 x 145mm (14" x 6")', 14, 6),
    (350, 175, '345 x 170mm (14" x 7")', 14, 7),
    (350, 200, '345 x 195mm (14" x 8")', 14, 8),
    (350, 225, '345 x 220mm (14" x 9")', 14, 9),
    (350, 250, '345 x 245mm (14" x 10")',14,10),
    (350, 275, '345 x 270mm (14" x 11")',14,11),
    (350, 300, '345 x 295mm (14" x 12")',14,12),
    (350, 330, '345 x 325mm (14" x 13")',14,13),
    (350, 350, '345 x 345mm (14" x 14")',14,14),

    # 15" group — sawn 375mm / planed 370mm (Alvin confirmed)
    (375, 38,  '370 x 33mm (15" x 1.5")',15, 1.5),
    (375, 25,  '370 x 20mm (15" x 1")',  15, 1),
    (375, 50,  '370 x 45mm (15" x 2")',  15, 2),
    (375, 75,  '370 x 70mm (15" x 3")',  15, 3),
    (375, 100, '370 x 95mm (15" x 4")',  15, 4),
    (375, 125, '370 x 120mm (15" x 5")', 15, 5),
    (375, 150, '370 x 145mm (15" x 6")', 15, 6),
    (375, 175, '370 x 170mm (15" x 7")', 15, 7),
    (375, 200, '370 x 195mm (15" x 8")', 15, 8),
    (375, 225, '370 x 220mm (15" x 9")', 15, 9),
    (375, 250, '370 x 245mm (15" x 10")',15,10),
    (375, 275, '370 x 270mm (15" x 11")',15,11),
    (375, 300, '370 x 295mm (15" x 12")',15,12),
    (375, 330, '370 x 325mm (15" x 13")',15,13),
    (375, 350, '370 x 345mm (15" x 14")',15,14),
    (375, 375, '370 x 370mm (15" x 15")',15,15),

    # 16" group — sawn 400mm / planed 395mm
    (400, 38,  '395 x 33mm (16" x 1.5")',16, 1.5),
    (400, 25,  '395 x 20mm (16" x 1")',  16, 1),
    (400, 50,  '395 x 45mm (16" x 2")',  16, 2),
    (400, 75,  '395 x 70mm (16" x 3")',  16, 3),
    (400, 100, '395 x 95mm (16" x 4")',  16, 4),
    (400, 125, '395 x 120mm (16" x 5")', 16, 5),
    (400, 150, '395 x 145mm (16" x 6")', 16, 6),
    (400, 175, '395 x 170mm (16" x 7")', 16, 7),
    (400, 200, '395 x 195mm (16" x 8")', 16, 8),
    (400, 225, '395 x 220mm (16" x 9")', 16, 9),
    (400, 250, '395 x 245mm (16" x 10")',16,10),
    (400, 275, '395 x 270mm (16" x 11")',16,11),
    (400, 300, '395 x 295mm (16" x 12")',16,12),
    (400, 330, '395 x 325mm (16" x 13")',16,13),
    (400, 350, '395 x 345mm (16" x 14")',16,14),
    (400, 375, '395 x 370mm (16" x 15")',16,15),
    (400, 400, '395 x 395mm (16" x 16")',16,16),
]

# 1.5" thickness entries — add to all existing groups 3" and above
_1p5_entries = []
for _nw, _sw in [(3,75),(4,100),(5,125),(6,150),(7,175),(8,200),(9,225),
                  (10,250),(11,275),(12,300),(13,330),(14,350)]:
    _pw = {3:70,4:95,5:120,6:145,7:170,8:195,9:220,
           10:245,11:270,12:295,13:325,14:345}[_nw]
    _1p5_entries.append((_sw, 38, f'{_pw} x 33mm ({_nw}" x 1.5")', _nw, 1.5))

STANDARD_SIZES = STANDARD_SIZES + _1p5_entries


# Trade mm → nominal inch lookup (for odd size 7200 formula)
TRADE_MM_TO_INCH = {
    # 1"
    20:1,  25:1,
    # 2"
    43:2,  45:2,  50:2,  51:2,
    # 3"
    70:3,  75:3,  76:3,
    # 4"
    93:4,  95:4,  100:4, 102:4,
    # 5"
    117:5, 120:5, 125:5, 127:5,
    # 6"
    143:6, 145:6, 150:6, 152:6,
    # 7"
    168:7, 170:7, 175:7, 178:7,
    # 8"
    193:8, 195:8, 200:8, 203:8,
    # 9"  — sawn 225mm / planed 220mm
    218:9, 220:9, 225:9, 229:9,
    # 10"
    243:10, 245:10, 250:10, 254:10,
    # 11"
    268:11, 270:11, 275:11, 279:11,
    # 12" — sawn 300mm / planed 295mm (also legacy 305/300)
    293:12, 295:12, 300:12, 305:12,
    # 13" — sawn 330mm / planed 325mm (Alvin override)
    323:13, 325:13, 330:13,
    # 14" — sawn 350mm / planed 345mm (Alvin confirmed)
    343:14, 345:14, 350:14,
    # 15" — sawn 375mm / planed 370mm (Alvin confirmed)
    368:15, 370:15, 375:15,
    # 16" — sawn 400mm / planed 395mm
    393:16, 395:16, 400:16,
    # 1.5" — sawn 38mm / planed 33mm
    33:1.5, 38:1.5,
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

def m_to_half_ft(l_m):
    """Convert metres to ft, ceiling to nearest 0.5ft.
    Used for free type length — gives user more granular options.
    e.g. 1.6m → 5.249ft → 5.5ft
    """
    ft = l_m * 3.28084
    return math.ceil(ft * 2) / 2

def snap_to_trade_length(l_m):
    """Ceil raw metre value to nearest trade-standard metre (from FT_TO_M).
    Used after Quick Fill so Len field shows clean trade length.
    e.g. 1050mm → 1.05m → 1.2m (4ft), 1600mm → 1.6m → 1.8m (6ft)
    """
    ft = l_m * 3.28084
    for f in sorted(FT_TO_M.keys()):
        if f >= ft - 0.01:
            return FT_TO_M[f]
    return FT_TO_M[22]

# QB sizes only (exclude 5", 7", 11" odd groups)
QB_SIZES  = STANDARD_SIZES   # all 105 sizes in QB dropdown
ODD_SIZES = STANDARD_SIZES   # all 105 sizes in Odd Size suggest

# All sizes for Odd Size dropdown (full list)

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

def suggest_quote_size(cust_w_mm, cust_h_mm, compare_sawn=False):
    """Find nearest ODD_SIZES entry whose dims >= customer dimensions.
    compare_sawn=True  → compare against sawn dims (entry[0], entry[1])
                         use when customer supplies sawn/nominal size
    compare_sawn=False → compare against planed dims from display label
                         use when customer supplies finished/planed size needed
    """
    import re
    def planed_dims(lbl):
        m = re.match(r'(\d+)\s*x\s*(\d+)mm', lbl)
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    best = None; best_dist = float('inf')
    for entry in ODD_SIZES:
        if compare_sawn:
            # entry = (sawn_w, sawn_h, label, nom_w, nom_h)
            ew, eh = entry[0], entry[1]
        else:
            ew, eh = planed_dims(entry[2])
        if ew >= cust_w_mm and eh >= cust_h_mm:
            dist = (ew - cust_w_mm) + (eh - cust_h_mm)
            if dist < best_dist:
                best_dist = dist; best = entry
    if best is None:
        for entry in ODD_SIZES:
            if compare_sawn:
                ew, eh = entry[0], entry[1]
            else:
                ew, eh = planed_dims(entry[2])
            dist = abs(ew - cust_w_mm) + abs(eh - cust_h_mm)
            if dist < best_dist:
                best_dist = dist; best = entry
    return best

def pcs_per_ton(w_mm, h_mm, ft):
    """Calculate pcs/ton from dimensions. Uses volume-weight method."""
    m   = ft_to_m_display(ft)
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
    # Birch base price shown in the reference table = the 10+ sheet rate.
    # Actual price used when adding to order depends on qty — see PLY_SELL_TIERS below.
    "Birch Plywood":         {15:98.0,  18:118.0},
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
    # TODO (Alvin): cost price to be updated — placeholder S$0.00 means profit/margin
    # will show as 100% until this is filled in. Don't quote off this until updated.
    "Birch Plywood":         {15:0.0,   18:0.0},
}
# Tiered selling price — ONLY for grades where price/sheet changes based on qty
# ordered (unlike PLY_MOQ below, which bumps qty up but keeps price fixed).
# sell_high_qty applies when qty >= moq_threshold; sell_low_qty applies otherwise.
PLY_SELL_TIERS = {
    "Birch Plywood": {
        15: {"moq_threshold": 10, "sell_high_qty": 98.0,  "sell_low_qty": 108.0},
        18: {"moq_threshold": 10, "sell_high_qty": 118.0, "sell_low_qty": 128.0},
    }
}
def get_tiered_sell_price(grade, thk, qty):
    """Returns the tiered price for (grade, thk) at the given qty, or None if
    this grade/thickness has no tiered pricing (use PLY_SELL as normal)."""
    tier = PLY_SELL_TIERS.get(grade, {}).get(thk)
    if not tier:
        return None
    return tier["sell_high_qty"] if qty >= tier["moq_threshold"] else tier["sell_low_qty"]
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
    "Birch Plywood":         {},   # no qty-bump MOQ — price tier handles this instead
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
    "cca_colour": "Brown — TimberTone",
    "cca_rate": 5.0,
    "sel_grade":   "MR China",
    "odd_cthk": None, "odd_cwid": None, "odd_clen": None,
    "odd_qthk": None, "odd_qwid": None, "odd_qlen": None,
    "odd_ctu": "mm", "odd_cwu": "mm", "odd_clu": "m", "odd_dim_type": "Sawn",
    "odd_sp":  "Kapur",
    "odd_qsize_label": None,
    "odd_qft": 8,
    "odd_suggest": None,
    "odd_accept_count": 0,
    "odd_qty": 1,
    "odd_accepted": False,
    "odd_acc_lbl": None, "odd_acc_full": None,
    "odd_acc_w_mm": None, "odd_acc_h_mm": None, "odd_acc_ft": None,
    "odd_qmode": "dropdown",
    "odd_qthk_free": None, "odd_qwid_free": None, "odd_qlen_free": None,
    "odd_qlu_free": "m",
    "odd_quickfill": "",
    "qf_fill_key": 0,
    "cust_name": "", "cust_mobile": "",
    "q_ready":   False, "q_reply":   "", "q_total":   0.0, "q_cost":   0.0, "q_nitem": 0, "q_log":   [],
    "odd_ready": False, "odd_reply": "", "odd_total": 0.0, "odd_cost": 0.0, "odd_nitem":0, "odd_log": [],
    "ply_ready": False, "ply_reply": "", "ply_total": 0.0, "ply_cost": 0.0, "ply_nitem":0, "ply_log": [],
    "comb_ready": False, "comb_reply": "", "comb_total": 0.0, "comb_cost": 0.0, "comb_nitem": 0, "comb_log": [],
    "hist_search_val": "",
    "hist_search_ver": 0,
    "rate_reset_key": 0,
    "cust_form_key": 0,
    "qrc_search": "",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def reset_all():
    """Full factory reset — clears all state, rates snap back to defaults."""
    _prev_rk = st.session_state.get("rate_reset_key", 0)
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    # Set rate_reset_key to a new value so rate widgets get fresh keys
    st.session_state["rate_reset_key"] = _prev_rk + 1
    st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="app-header">
  <div class="app-header-title">🪵 Timber AI Assistant
    <span style="background:#1D9E75;color:white;font-size:13px;padding:2px 8px;border-radius:99px;margin-left:8px;vertical-align:middle">V33</span>
  </div>
  <div class="app-header-sub">Professional Quoting System &nbsp;·&nbsp; Prices in SGD</div>
</div>
""", unsafe_allow_html=True)

# Default rate values — used as value= args in number_input widgets
DEFAULT_RATES = {"Kapur": 3800, "Balau": 5500, "Chengal": 6000, "Mixed Keruing": 650, "Pure Keruing": 1000}
DEFAULT_CCA_COLOUR = "Brown — TimberTone"
DEFAULT_CCA_RATE   = 5.0

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
        st.session_state.cca_colour = DEFAULT_CCA_COLOUR
        st.session_state.cca_rate = DEFAULT_CCA_RATE
        st.toast("✅ Rates reset to defaults (incl. CCA)", icon="↩")
        st.rerun()

species_rate = {
    "Kapur": kapur_rate, "Balau": balau_rate, "Chengal": cheng_rate,
    "Mixed Keruing": mkeruing_rate, "Pure Keruing": pkeruing_rate
}

# CCA Treatment inputs — shared across QB, Odd Size, Plywood tabs
cc1, cc2, cc3 = st.columns([2, 2, 7])
with cc1:
    _cca_colour_opts = ["Brown — TimberTone", "Colourless"]
    cca_colour = st.selectbox(
        "CCA Colour", _cca_colour_opts,
        index=_cca_colour_opts.index(st.session_state.cca_colour),
        key="cca_colour_sel"
    )
    st.session_state.cca_colour = cca_colour
with cc2:
    cca_rate = st.number_input(
        "CCA Rate (S$/pc)", min_value=0.0,
        value=float(st.session_state.cca_rate),
        step=0.5, format="%.2f", key=f"cca_rate_inp_{_rk}"
    )
    st.session_state.cca_rate = cca_rate
st.divider()

# ============================================================
# ============================================================
# ============================================================
# FUNCTIONS: Gist helpers, calc engine, parser, UI utilities
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

# ---- Plywood cost overrides + rate change log (same gist, two more files) ----
def _ply_override_key(grade, thk):
    return f"{grade}|{thk}"

def load_ply_cost_overrides():
    """Returns {"Grade|thk": cost} for any grade/thickness with a manually
    updated cost price. Falls back to {} if the gist file doesn't exist yet
    (e.g. before the first cost update is ever made)."""
    gist_id = st.secrets.get("gist_id", "")
    if not gist_id: return {}
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}",
                         headers=gist_headers(), timeout=15)
        if r.status_code == 200:
            files = r.json().get("files", {})
            if "ply_cost_overrides.json" not in files: return {}
            raw = files["ply_cost_overrides.json"]["content"]
            if not raw or raw.strip() == "{}": return {}
            return json.loads(raw)
    except Exception:
        pass
    return {}

def save_ply_cost_overrides(overrides):
    gist_id = st.secrets.get("gist_id", "")
    if not gist_id: st.error("❌ gist_id not set in Streamlit secrets."); return False
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=gist_headers(),
            json={"files": {"ply_cost_overrides.json": {"content": json.dumps(overrides, indent=2)}}},
            timeout=15)
        return r.status_code == 200
    except Exception as e:
        st.error(f"❌ Network error: {str(e)}"); return False

def load_ply_rate_log():
    gist_id = st.secrets.get("gist_id", "")
    if not gist_id: return []
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}",
                         headers=gist_headers(), timeout=15)
        if r.status_code == 200:
            files = r.json().get("files", {})
            if "ply_rate_log.json" not in files: return []
            raw = files["ply_rate_log.json"]["content"]
            if not raw or raw.strip() == "[]": return []
            return json.loads(raw)
    except Exception:
        pass
    return []

def save_ply_rate_log(log):
    gist_id = st.secrets.get("gist_id", "")
    if not gist_id: return False
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=gist_headers(),
            json={"files": {"ply_rate_log.json": {"content": json.dumps(log, indent=2)}}},
            timeout=15)
        return r.status_code == 200
    except Exception as e:
        st.error(f"❌ Network error: {str(e)}"); return False

def update_ply_cost(grade, thk, new_cost):
    """Persists a new cost price for (grade, thk): updates the live override
    and appends one entry to the rate change log. Returns True on success."""
    overrides = load_ply_cost_overrides()
    key = _ply_override_key(grade, thk)
    old_cost = overrides.get(key, PLY_COST.get(grade, {}).get(thk, 0.0))
    if round(float(old_cost), 2) == round(float(new_cost), 2):
        return True  # no actual change, nothing to save
    overrides[key] = round(float(new_cost), 2)
    ok1 = save_ply_cost_overrides(overrides)
    log = load_ply_rate_log()
    log.insert(0, {
        "date": now_sgt().strftime("%d %b %Y"), "time": now_sgt().strftime("%H:%M"),
        "grade": grade, "thk": thk, "old_cost": round(float(old_cost), 2), "new_cost": round(float(new_cost), 2)
    })
    ok2 = save_ply_rate_log(log)
    if ok1 and ok2:
        st.session_state.ply_cost_overrides = overrides  # refresh in-memory cache
    return ok1 and ok2

def effective_ply_cost(grade, thk):
    """Live cost price for (grade, thk): manual override if one exists, else the code default."""
    overrides = st.session_state.get("ply_cost_overrides", {})
    key = _ply_override_key(grade, thk)
    if key in overrides:
        return overrides[key]
    return PLY_COST.get(grade, {}).get(thk, 0.0)

if "ply_cost_overrides" not in st.session_state:
    st.session_state.ply_cost_overrides = load_ply_cost_overrides()

def save_quote(customer, mobile, total, items, quote_text, cost_total=0, quote_type="Quote", valid_days=None):
    history = load_history()
    profit  = round(total - cost_total, 2)
    margin  = round((profit / total * 100), 1) if total > 0 else 0
    _valid_days = valid_days if valid_days is not None else QUOTE_VALIDITY_DAYS
    entry   = {
        "id":       now_sgt().strftime("%Y%m%d_%H%M%S"),
        "date":     now_sgt().strftime("%d %b %Y"),
        "time":     now_sgt().strftime("%H:%M"),
        "customer": customer.strip() if customer.strip() else "—",
        "mobile":   mobile.strip()   if mobile.strip()   else "—",
        "type":     quote_type,
        "items": items, "total": total, "cost": cost_total,
        "profit": profit, "margin": margin, "text": quote_text,
        "closed": False, "closed_date": "",
        "valid_until": (now_sgt() + timedelta(days=_valid_days)).strftime("%d %b %Y")
    }
    history.insert(0, entry)
    history = history[:200]
    return save_history(history)

def effective_valid_until(q):
    """Returns the quote's valid_until as a datetime, falling back to
    date-saved + QUOTE_VALIDITY_DAYS for quotes saved before valid_until
    existed. Returns None if neither can be determined."""
    valid_until_str = q.get("valid_until", "")
    if not valid_until_str:
        saved_date_str = q.get("date", "")
        if not saved_date_str:
            return None
        try:
            saved_date = datetime.strptime(saved_date_str, "%d %b %Y")
        except ValueError:
            return None
        return saved_date + timedelta(days=QUOTE_VALIDITY_DAYS)
    try:
        return datetime.strptime(valid_until_str, "%d %b %Y")
    except ValueError:
        return None

def quote_is_expired(q):
    """True if the quote's validity date has passed."""
    valid_until = effective_valid_until(q)
    if valid_until is None:
        return False
    return now_sgt().replace(tzinfo=None) > valid_until

# Preset follow-up tags a quote can carry. Grouped by category, but a quote
# may carry any combination of tags at once (e.g. "WhatsApp" + "Tender").
QUOTE_TAG_DEFS = {
    "src_email":       {"category": "Source", "label": "Email",        "emoji": "📧", "color": "gray"},
    "src_whatsapp":    {"category": "Source", "label": "WhatsApp",     "emoji": "💬", "color": "gray"},
    "src_phone":       {"category": "Source", "label": "Phone",        "emoji": "☎️", "color": "gray"},
    "src_walkin":      {"category": "Source", "label": "Walk-in",      "emoji": "🚶", "color": "gray"},
    "stage_tender":    {"category": "Stage",  "label": "Tender",       "emoji": "📋", "color": "violet"},
    "stage_awarded":   {"category": "Stage",  "label": "Awarded",      "emoji": "🏆", "color": "violet"},
    "stage_direct":    {"category": "Stage",  "label": "Direct",       "emoji": "➡️", "color": "violet"},
    "status_potential":     {"category": "Status", "label": "Potential",     "emoji": "🌱", "color": "green"},
    "status_not_interested":{"category": "Status", "label": "Not Interested","emoji": "😞", "color": "red"},
    "status_call_back":     {"category": "Status", "label": "Call Back",     "emoji": "📞", "color": "blue"},
}

def tag_option_label(tag_key):
    """Dropdown display label, e.g. 'Source: WhatsApp'."""
    d = QUOTE_TAG_DEFS.get(tag_key, {})
    return f"{d.get('category','')}: {d.get('emoji','')} {d.get('label',tag_key)}"

def tag_badges_markdown(tags):
    """Returns a string of Streamlit colored-background badges for the given tag keys."""
    parts = []
    for t in tags or []:
        d = QUOTE_TAG_DEFS.get(t)
        if not d:
            continue
        parts.append(f" &nbsp;:{d['color']}-background[{d['emoji']} {d['label']}]")
    return "".join(parts)

def set_quote_tags(qid, tags):
    """Saves the given list of tag keys onto the quote. Returns True on success."""
    history = load_history()
    found = False
    for q in history:
        if q.get("id") == qid:
            q["tags"] = tags
            found = True
            break
    if not found:
        return False
    return save_history(history)

def mark_quote_closed(qid):
    """Marks a quote as closed with today's SGT date. Returns True on success."""
    history = load_history()
    found = False
    for q in history:
        if q.get("id") == qid:
            q["closed"] = True
            q["closed_date"] = now_sgt().strftime("%d %b %Y")
            found = True
            break
    if not found:
        return False
    return save_history(history)

def delete_quote(qid):
    history = load_history()
    save_history([q for q in history if q.get("id") != qid])

def find_recent_customers(query, limit=5):
    """Returns up to `limit` unique (name, mobile) pairs from History, most
    recent first, matching `query` anywhere in the name or mobile number.
    Empty query returns the most recent unique customers overall."""
    history = load_history()
    query = query.strip().lower()
    seen = set()
    results = []
    for entry in history:
        name = entry.get("customer", "—")
        mobile = entry.get("mobile", "—")
        if name == "—" and mobile == "—":
            continue
        key = (name, mobile)
        if key in seen:
            continue
        if query and query not in name.lower() and query not in mobile.lower():
            continue
        seen.add(key)
        results.append({"name": name, "mobile": mobile, "date": entry.get("date", "")})
        if len(results) >= limit:
            break
    return results

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

def cca_combined_price(base_price, cca_on, cca_rate):
    """Single source of truth for merging the CCA surcharge into a unit
    price. If a CCA-style pricing rule ever changes, this is the one place
    to update it — used everywhere the surcharge is applied."""
    return ceil_10cents(base_price + cca_rate) if cca_on else base_price

def price_line_with_cca(base_price, cca_on, cca_rate, qty, unit="pc", unit_plural=None):
    """Builds an item card's price line, showing the CCA breakdown (base +
    surcharge = combined) whenever CCA is on, so the live card always
    matches what the generated quote will say. The surcharge is highlighted
    in green so it's easy to spot at a glance."""
    unit_plural = unit_plural or (unit + "s")
    combined = cca_combined_price(base_price, cca_on, cca_rate)
    total = round(combined * qty, 2)
    if cca_on:
        cca_highlight = (
            f'<span style="background:#CCFF66;color:#1a1a1a;padding:0 4px;'
            f'border-radius:2px">S${cca_rate:.2f} CCA</span>'
        )
        return (f'S${base_price}/{unit} + {cca_highlight} = <b>S${combined}</b>/{unit} '
                f'× {qty} {unit_plural} = <b>S${total:,.2f}</b>')
    return f'S${base_price}/{unit} × {qty} {unit_plural} = <b>S${total:,.2f}</b>'

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

def build_reply(lines, total, is_timber=True, is_plywood=False, extra_note="", valid_days=QUOTE_VALIDITY_DAYS):
    """
    Build customer reply text.
    - Total line removed (per-line subtotals are sufficient)
    - Tolerances split by product type:
        Timber:  Thickness/Width +-1~2mm  |  Length +-25~50mm
        Plywood: Thickness +-0.8~1.2mm
        Mixed:   both sections labelled
    - Validity stated as a duration (e.g. "Quote valid : 7 days"), not a fixed end date
    """
    out = list(lines)
    out.append("\nTolerances:")
    if is_timber and is_plywood:
        # Mixed quote
        out.append("Timber:")
        out.append("- Thickness/Width: +-1~2mm")
        out.append("- Length: +-25~50mm")
        out.append("Plywood:")
        out.append("- Thickness: +-0.8~1.2mm")
    elif is_plywood:
        out.append("- Thickness: +-0.8~1.2mm")
    else:
        # Timber only (default)
        out.append("- Thickness/Width: +-1~2mm")
        out.append("- Length: +-25~50mm")
    if extra_note:
        out.append(extra_note)
    out.append("\nDelivery / Self Collection:")
    out.append("30 Kranji Loop (Blk A) #04-05")
    out.append("TimMac @ Kranji S739570")
    out.append(f"\nQuote valid : {valid_days} days")
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
    """Parse a free-text dimension string into (thk_mm, wid_mm, len_mm).

    Handles mixed units per token — each number evaluated independently:
      - suffix 'in', 'IN', or '"'  → value × 25   (trade: 1" = 25mm)
      - suffix 'ft', 'FT', or "'"  → value × 300  (trade: 1' = 12" = 300mm)
      - suffix 'mm', 'MM' or none  → value as mm
    Examples:
      10inx8inx1600mm  →  t=250, w=200, l=1600
      10"x8"x20"       →  t=250, w=200, l=500
      8"x4"x14'        →  t=100, w=200, l=4200  (14ft → 4.2m)
      200x400x1600     →  t=200, w=400, l=1600
    Returns dict with keys 't','w','l' (floats in mm), or None on failure.
    """
    import re

    def _to_mm(val_str, suffix):
        v = float(val_str)
        if suffix.upper().replace('"','IN') in ('IN','IN',''):
            # detect if suffix is inch
            pass
        return v

    # Extract tokens: each token is (number, unit_suffix)
    # Pattern: optional label (T/W/L), number, optional unit (in/ft/mm/"/')
    token_re = re.compile(
        r'(?:[TWL]\s*)?'          # optional label prefix
        r'(\d+(?:\.\d+)?)'        # number
        r'\s*'
        r'(in|IN|ft|FT|mm|MM|"|\')?',   # optional unit suffix
        re.IGNORECASE
    )

    tokens = []
    for m in token_re.finditer(raw):
        num = m.group(1)
        unit = (m.group(2) or '').strip().upper()
        if not num:
            continue
        v = float(num)
        if unit in ('IN', '"'):
            v = round(v * 25, 1)    # trade: 1" = 25mm
        elif unit in ('FT', "'"):
            v = round(v * 300, 1)   # trade: 1' = 12" = 300mm
        # mm or no suffix → keep as mm
        tokens.append(v)

    tokens = [t for t in tokens if t > 0]

    if len(tokens) == 3:
        t, w, l = sorted(tokens)
        return {"t": t, "w": w, "l": l}
    if len(tokens) == 2:
        t, w = sorted(tokens)
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
    if u in ["in","inch",'"']: return float(value) * 25
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
# SHARED UI HELPERS (V33) — used by Quote Builder / Odd Size /
# Plywood tabs to avoid triplicated card/pricing/output code.
# ============================================================

def cca_badge_html(cca_on):
    return (
        '<span style="font-size:11px;padding:1px 8px;border-radius:99px;'
        'background:#1D9E75;color:white;margin-left:6px">✓ CCA</span>'
        if cca_on else ""
    )

def cca_status_pill(items):
    """Small at-a-glance pill showing whether any item in this list has CCA
    treatment on. Returns "" (render nothing) if none do."""
    n_cca = sum(1 for it in (items or []) if it.get("cca", False))
    if n_cca == 0:
        return ""
    return (
        f'<span style="font-size:11px;padding:1px 8px;border-radius:99px;'
        f'background:#1D9E75;color:white;margin-left:6px">🧪 {n_cca} item'
        f'{"s" if n_cca != 1 else ""} with CCA</span>'
    )

def clipboard_copy_button(text, key, label="📋 Copy as TXT"):
    """Real clipboard copy (navigator.clipboard.writeText, with an
    execCommand fallback) instead of a file download, so staff can paste
    straight into WhatsApp/email.
    Uses components.v1.html (not st.markdown) because Streamlit's markdown
    sanitizer strips inline onclick="..." attributes even with
    unsafe_allow_html=True — the button would render but do nothing."""
    import streamlit.components.v1 as components
    btn_id = f"copybtn_{key}"
    # </script> inside the quote text would otherwise break out of our
    # <script> block, so neutralise any "</" sequence.
    js_text = json.dumps(text).replace("</", "<\\/")
    label_js = json.dumps(label)
    html_code = f"""
    <button id="{btn_id}" style="width:100%;padding:0.5rem 1rem;
        border-radius:0.5rem;border:1px solid rgba(128,128,128,0.4);
        background:transparent;color:inherit;cursor:pointer;font-size:14px;
        height:2.5rem;box-sizing:border-box;font-family:inherit;">{label}</button>
    <style>
        body {{ margin:0; color:#31333F; }}
        @media (prefers-color-scheme: dark) {{ body {{ color:#fafafa; }} }}
    </style>
    <script>
        (function() {{
            var btn = document.getElementById("{btn_id}");
            var textToCopy = {js_text};
            var origLabel = {label_js};
            function fallbackCopy(t) {{
                var ta = document.createElement("textarea");
                ta.value = t;
                ta.style.position = "fixed";
                ta.style.opacity = "0";
                document.body.appendChild(ta);
                ta.focus(); ta.select();
                var ok = false;
                try {{ ok = document.execCommand("copy"); }} catch (e) {{ ok = false; }}
                document.body.removeChild(ta);
                return ok;
            }}
            function showResult(ok) {{
                btn.innerText = ok ? "✅ Copied!" : "⚠️ Copy failed";
                setTimeout(function() {{ btn.innerText = origLabel; }}, 1500);
            }}
            btn.addEventListener("click", function() {{
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(textToCopy)
                        .then(function() {{ showResult(true); }})
                        .catch(function() {{ showResult(fallbackCopy(textToCopy)); }});
                }} else {{
                    showResult(fallbackCopy(textToCopy));
                }}
            }});
        }})();
    </script>
    """
    components.html(html_code, height=48)

def render_item_card(title, pills, detail_line, price_line, warn=False,
                      warn_note=None, footer_note=None, badge_html=""):
    if warn:
        bg, border, text, sub, pill_bg = "#FAEEDA", "#FAC775", "#412402", "#633806", "#FAC775"
    else:
        bg, border, text, sub, pill_bg = (
            "var(--color-background-primary)", "var(--color-border-tertiary)",
            "var(--color-text-primary)", "var(--color-text-secondary)",
            "var(--color-background-secondary)"
        )
    pill_html = "".join(
        f'<span style="font-size:11px;padding:1px 8px;border-radius:99px;'
        f'background:{pill_bg};color:{text if warn else sub};'
        f'border:0.5px solid {border};margin-left:4px">{p}</span>'
        for p in pills
    )
    detail_html = (
        f'<div style="font-size:12px;color:{sub};margin-top:2px">{detail_line}</div>'
        if detail_line else ""
    )
    footer_html = (
        f'<div style="border-top:0.5px solid {border};margin-top:7px;'
        f'padding-top:6px;font-size:12px;color:{sub}">{footer_note}</div>'
        if footer_note else ""
    )
    warn_html = (
        f'<div style="font-size:11px;color:#854F0B;margin-top:3px">⚠️ {warn_note}</div>'
        if (warn and warn_note) else ""
    )
    st.markdown(
        f'<div style="background:{bg};border:0.5px solid {border};'
        f'border-radius:var(--border-radius-md);padding:10px 14px;margin-bottom:4px">'
        f'<div style="font-weight:500;font-size:14px;color:{text};white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis">{title}{pill_html}{badge_html}</div>'
        f'{detail_html}'
        f'<div style="font-size:13px;color:{sub};margin-top:4px">{price_line}</div>'
        f'{warn_html}{footer_html}'
        f'</div>',
        unsafe_allow_html=True
    )

def render_quote_output(prefix, extra_clear_keys=None, save_type=None,
                         show_metrics=True, show_staff_log=True,
                         show_copy=True, show_clear=True, reply_height=350,
                         file_prefix=None):
    """Renders staff log + reply textarea + action buttons.
    save_type=None disables the Save to History button.
    show_metrics/show_staff_log/show_copy/show_clear let a tab opt out of
    parts it doesn't use (e.g. Odd Size has no staff log display today)."""
    ss = st.session_state
    grand_total = ss[f"{prefix}_total"]; cost_total = ss[f"{prefix}_cost"]
    if show_metrics:
        st.subheader("Quote Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Items", ss[f"{prefix}_nitem"])
        with m2: st.metric("Grand Total", f"S${grand_total:,.2f}")
        with m3: st.metric("Est. Profit", f"S${round(grand_total - cost_total, 2):,.2f}")
        with m4: st.metric("Est. Margin", f"{round((grand_total - cost_total) / grand_total * 100, 1) if grand_total > 0 else 0}%")
    if show_staff_log:
        render_staff_log(ss[f"{prefix}_log"], grand_total, cost_total)
    st.divider()
    st.subheader("Customer Reply (edit before sending)")
    edited = st.text_area("", ss[f"{prefix}_reply"], height=reply_height, key=f"cust_reply_{prefix}")

    n_cols = (1 if save_type else 0) + (1 if show_copy else 0) + (1 if show_clear else 0)
    cols = st.columns(max(n_cols, 1))
    col_i = 0
    if save_type:
        with cols[col_i]:
            if st.button("💾 Save to History", type="primary", use_container_width=True, key=f"save_{prefix}"):
                ok = save_quote(ss.cust_name, ss.cust_mobile, grand_total,
                    ss[f"{prefix}_nitem"], edited, cost_total, quote_type=save_type,
                    valid_days=ss.get(f"{prefix}_valid_days", QUOTE_VALIDITY_DAYS))
                if ok: st.success("✅ Saved!")
                else:  st.error("❌ Could not save.")
        col_i += 1
    if show_copy:
        with cols[col_i]:
            clipboard_copy_button(edited, key=prefix)
        col_i += 1
    if show_clear:
        with cols[col_i]:
            if st.button("🗑️ Clear Quote", use_container_width=True, key=f"clear_reply_{prefix}"):
                for k in (extra_clear_keys or []):
                    ss[k] = []
                ss[f"{prefix}_ready"] = False
                st.rerun()

# ============================================================
# ============================================================
# ============================================================
# UI TABS: Quote Builder, Odd Size, Plywood, Suppliers, History
# AI Parser and Plywood Cut-to-Size removed — built as separate apps
# ============================================================

if "expiry_banner_checked" not in st.session_state:
    _banner_history = load_history()
    _cutoff = now_sgt().replace(tzinfo=None) - timedelta(days=7)
    _recent_expired = 0
    _recent_expired_list = []
    for _q in _banner_history:
        if _q.get("closed", False):
            continue
        if not quote_is_expired(_q):
            continue
        _vu_str = _q.get("valid_until", "")
        try:
            _vu = datetime.strptime(_vu_str, "%d %b %Y") if _vu_str else None
        except ValueError:
            _vu = None
        # Only count quotes that expired recently (within the last 7 days),
        # not every stale quote from months ago — this is a "new this week" notice.
        if _vu is not None and _vu >= _cutoff:
            _recent_expired += 1
            _recent_expired_list.append(_q)
    _recent_expired_list.sort(key=lambda q: effective_valid_until(q))
    st.session_state.expiry_banner_count = _recent_expired
    st.session_state.expiry_banner_list = _recent_expired_list
    st.session_state.expiry_banner_checked = True

if st.session_state.get("expiry_banner_count", 0) > 0:
    _n = st.session_state.expiry_banner_count
    st.error(f"❌ {_n} quote{'s' if _n != 1 else ''} expired this week — check the History tab to follow up.")

if "expiring_soon_checked" not in st.session_state:
    _soon_history = load_history()
    _today = now_sgt().date()
    _soon_cutoff = add_working_days(_today, EXPIRING_SOON_WORKING_DAYS)
    _soon_list = []
    for _q in _soon_history:
        if _q.get("closed", False):
            continue
        if quote_is_expired(_q):
            continue
        _vu = effective_valid_until(_q)
        if _vu is None:
            continue
        if _today <= _vu.date() <= _soon_cutoff:
            _soon_list.append(_q)
    _soon_list.sort(key=lambda q: effective_valid_until(q))
    st.session_state.expiring_soon_list = _soon_list
    st.session_state.expiring_soon_count = len(_soon_list)
    st.session_state.expiring_soon_checked = True

def render_customer_section(key_prefix):
    """Quick repeat customer search + Customer Details fields. Shared by
    QB and Plywood (Odd Size keeps its own simpler fields, no search box,
    per its existing design) so name/mobile stay in sync across tabs.
    key_prefix keeps each tab's widget keys unique — Streamlit renders
    every tab's content on every script run, not just the visible one."""
    st.markdown("#### Quick repeat customer")
    qrc_query = st.text_input("Search by name or mobile", value=st.session_state.qrc_search,
        placeholder="e.g. Tan or 9123", key=f"qrc_search_inp_{key_prefix}", label_visibility="collapsed")
    st.session_state.qrc_search = qrc_query
    if qrc_query.strip():
        _matches = find_recent_customers(qrc_query, limit=5)
        if _matches:
            for _m in _matches:
                _mc1, _mc2 = st.columns([4, 1])
                with _mc1:
                    st.markdown(f'<div style="padding:8px 0"><b>{_m["name"]}</b><br>'
                                f'<span style="font-size:12px;color:var(--color-text-secondary)">'
                                f'{_m["mobile"]} · last quote {_m["date"]}</span></div>', unsafe_allow_html=True)
                with _mc2:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("Use", key=f"qrc_use_{key_prefix}_{_m['name']}_{_m['mobile']}", use_container_width=True):
                        st.session_state.cust_name = _m["name"]
                        st.session_state.cust_mobile = _m["mobile"]
                        st.session_state.cust_form_key += 1
                        st.session_state.qrc_search = ""
                        st.rerun()
        else:
            st.caption("No matching customers found in History.")
    st.divider()
    st.markdown("#### Customer Details")
    cd1, cd2 = st.columns(2)
    with cd1:
        cust_name = st.text_input("Customer Name / Company",
            value=st.session_state.cust_name,
            placeholder="e.g. ABC Construction Pte Ltd",
            key=f"cust_name_inp_{key_prefix}_{st.session_state.cust_form_key}")
        st.session_state.cust_name = cust_name
    with cd2:
        cust_mobile = st.text_input("Mobile Number",
            value=st.session_state.cust_mobile,
            placeholder="e.g. 9123 4567",
            key=f"cust_mobile_inp_{key_prefix}_{st.session_state.cust_form_key}")
        st.session_state.cust_mobile = cust_mobile
    st.divider()

_expired_n = st.session_state.get("expiry_banner_count", 0)
_soon_n = st.session_state.get("expiring_soon_count", 0)
_history_tab_label = "🕘 History"
if _expired_n > 0 and _soon_n > 0:
    _history_tab_label = f"🕘 History ({_expired_n} ❌ / {_soon_n} ⏰)"
elif _expired_n > 0:
    _history_tab_label = f"🕘 History ({_expired_n} ❌)"
elif _soon_n > 0:
    _history_tab_label = f"🕘 History ({_soon_n} ⏰)"

tab_quote, tab_odd, tab_ply, tab_combined, tab_sup, tab_hist = st.tabs([
    "📋 Quote Builder", "📐 Odd Size", "🪵 Plywood", "🔀 Combined",
    "🏭 Suppliers", _history_tab_label
])

# ============================================================
# TAB 1 — QUOTE BUILDER
# ============================================================
with tab_quote:
    render_customer_section("qb")
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
            f'padding:2px 8px;border-radius:99px;font-weight:600">{n_items}</span>'
            f'{cca_status_pill(st.session_state.order_items)}</div>',
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
            _cca_on = item.get("cca", False)

            render_item_card(
                title=f'{item["species"]} · {item["size"]}',
                pills=[f"@S${locked_rate:,}/ton"],
                detail_line=None,
                price_line=price_line_with_cca(locked_price, _cca_on, cca_rate, item["qty"]),
                warn=mixed_rates,
                warn_note=f'Different rate from other {item["species"]} items' if mixed_rates else None,
                badge_html=cca_badge_html(_cca_on),
            )
            ic1, ic2, ic3 = st.columns([9, 1, 1])
            with ic2:
                if st.button("CCA", key=f"cca_qb_{i}",
                             help="Toggle CCA anti-termite / insect borer treatment"):
                    st.session_state.order_items[i]["cca"] = not _cca_on
                    st.session_state.q_ready = False
                    st.rerun()
            with ic3:
                if st.button("🗑️", key=f"dt_{i}"):
                    st.session_state.order_items.pop(i)
                    st.session_state.q_ready = False
                    st.rerun()

        st.divider()
        q_valid_days = st.slider("Quote validity (days)", min_value=1, max_value=30,
            value=st.session_state.get("q_valid_days", QUOTE_VALIDITY_DAYS), key="q_valid_days")
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
            _has_cca = False
            for item in st.session_state.order_items:
                locked_rate = item["rate"]
                locked_raw, _, locked_price = calc_from_mm(
                    item["w_mm"], item["h_mm"], item["ft"], locked_rate,
                    item.get("nom_w"), item.get("nom_h")
                )
                _item_cca = item.get("cca", False)
                # Combined price = timber price/pc + CCA rate/pc (if CCA on)
                _combined_price = cca_combined_price(locked_price, _item_cca, cca_rate)
                gt = round(_combined_price * item["qty"], 2)
                grand_total += gt
                cost_est = round(gt * 0.85, 2); cost_total += cost_est
                profit = round(gt - cost_est, 2)
                margin_pct = round((profit / gt * 100), 1) if gt > 0 else 0
                _cca_badge_html = (
                    ' <span style="font-size:11px;padding:1px 8px;border-radius:99px;'
                    'background:#1D9E75;color:white;margin-left:6px">🧪 CCA</span>'
                    if _item_cca else ""
                )
                _price_rows = (
                    {
                        "Timber price/pc":   f"S${locked_price}",
                        "CCA rate/pc":       f"+ S${cca_rate:.2f} ({cca_colour})",
                        "Combined price/pc": f"S${_combined_price}",
                    } if _item_cca else
                    {"Price per piece": f"S${locked_price}"}
                )
                log_items.append({
                    "heading": f"{item['species']} timber · {item['size']}{_cca_badge_html}",
                    "rows": {
                        "Rate":            f"S${locked_rate:,}/ton",
                        "Pieces per ton":  str(round(locked_raw, 2)),
                        **_price_rows,
                        "Qty":             f"{item['qty']} pcs",
                        "Line total":      f"S${gt:,.2f}",
                    },
                    "profit_line": f"S${profit:,.2f}", "margin_pct": f"{margin_pct}%",
                    "small_qty": item["small_qty"]
                })
                if _item_cca:
                    _has_cca = True
                    customer_reply.append(
                        f"{item['species']} timber planed treated with anti-termite / insect borer treatment ({cca_colour})\n"
                        f"{item['size']} @ S${_combined_price}/pcs x {item['qty']} = S${gt:,.2f}"
                    )
                else:
                    customer_reply.append(
                        f"{item['species']} timber\n{item['size']} @ S${locked_price}/pcs x {item['qty']} = S${gt:,.2f}"
                    )
            grand_total = round(grand_total, 2); cost_total = round(cost_total, 2)
            _cca_note = "\n\nNote: After treatment, timber/plywood may be wet and may have some powder when dried." if _has_cca else ""
            reply_text = build_reply(customer_reply, grand_total, is_timber=True, is_plywood=False, extra_note=_cca_note, valid_days=q_valid_days)
            st.session_state.q_ready = True; st.session_state.q_reply  = reply_text
            st.session_state.q_total = grand_total; st.session_state.q_cost   = cost_total
            st.session_state.q_nitem = len(customer_reply); st.session_state.q_log = log_items

        if st.session_state.q_ready:
            render_quote_output("q", extra_clear_keys=["order_items"], save_type="Quote")
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
            value=st.session_state.cust_name, placeholder="e.g. ABC Construction Pte Ltd",
            key=f"odd_cust_name_inp_{st.session_state.cust_form_key}")
        st.session_state.cust_name = odd_cust_name
    with od_cd2:
        odd_cust_mobile = st.text_input("Mobile Number",
            value=st.session_state.cust_mobile, placeholder="e.g. 9123 4567",
            key=f"odd_cust_mobile_inp_{st.session_state.cust_form_key}")
        st.session_state.cust_mobile = odd_cust_mobile
    st.divider()

    # ── CSS for new layout ────────────────────────────────────
    st.markdown("""<style>
    .os-step{display:flex;gap:12px;align-items:flex-start;margin-bottom:12px}
    .os-num{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;
            justify-content:center;font-size:12px;font-weight:500;flex-shrink:0;margin-top:16px}
    .os-active{background:#1D9E75;color:#fff}
    .os-done{background:#E1F5EE;color:#0F6E56;border:0.5px solid #5DCAA5}
    .os-idle{background:#f0f0f0;color:#aaa}
    .os-sug{background:#E1F5EE;border:0.5px solid #5DCAA5;border-radius:8px;padding:10px 14px;flex:1}
    .os-step3{background:#E1F5EE;border:0.5px solid #5DCAA5;border-radius:8px;padding:10px 14px;flex:1}
    .os-idle-box{background:#f7f7f7;border-radius:8px;padding:10px 14px;flex:1;color:#aaa;font-size:13px}
    </style>""", unsafe_allow_html=True)

    # ── Row 0: Species / Rate / Reset ─────────────────────────
    _rrk = st.session_state.rate_reset_key
    _fk  = st.session_state.qf_fill_key
    r0c1, r0c2, r0c5, r0c3, r0c4 = st.columns([2, 2, 1.4, 1, 1])
    _prev_sp = st.session_state.odd_sp
    with r0c1: st.session_state.odd_sp = st.selectbox("Species", SPECIES, index=SPECIES.index(st.session_state.odd_sp), key="odd_sp_sel")
    # Auto-switch rate when species changes
    if st.session_state.odd_sp != _prev_sp:
        st.session_state.rate_reset_key += 1
        st.rerun()
    _rrk = st.session_state.rate_reset_key  # re-read after possible increment
    with r0c2: odd_rate = st.number_input("Rate (S$/ton)", min_value=0, value=species_rate[st.session_state.odd_sp], step=50, key=f"odd_rate_{_rrk}")
    with r0c5:
        st.session_state.odd_dim_type = st.radio(
            "Customer dim is", ["Sawn", "Planed"],
            index=["Sawn","Planed"].index(st.session_state.odd_dim_type),
            horizontal=True, key="odd_dim_type_radio",
            help="Sawn: customer gives rough/nominal size (e.g. 350mm = 14\"). Planed: customer needs that exact finished size.")
    with r0c3:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("↩ Reset rates", use_container_width=True, key="odd_reset_rates"):
            st.session_state.rate_reset_key += 1
            st.session_state.cca_colour = DEFAULT_CCA_COLOUR
            st.session_state.cca_rate = DEFAULT_CCA_RATE
            st.toast("✅ Rates reset to defaults (incl. CCA)", icon="↩")
            st.rerun()
    with r0c4:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Clear inputs", use_container_width=True, key="odd_clear_inputs"):
            _input_keys = {
                "odd_cthk": None, "odd_cwid": None, "odd_clen": None,
                "odd_ctu": "mm", "odd_cwu": "mm", "odd_clu": "m", "odd_dim_type": "Sawn",
                "odd_qsize_label": None, "odd_suggest": None,
                "odd_qft": 8, "odd_qty": 1, "odd_qmode": "dropdown",
                "odd_qthk_free": None, "odd_qwid_free": None,
                "odd_qlen_free": None, "odd_qlu_free": "m",
                "odd_accepted": False,
                "odd_acc_lbl": None, "odd_acc_full": None,
                "odd_acc_w_mm": None, "odd_acc_h_mm": None, "odd_acc_ft": None,
                "odd_quickfill": "",
            }
            for k, v in _input_keys.items():
                st.session_state[k] = v
            st.session_state.qf_fill_key   += 1
            st.session_state.rate_reset_key += 1
            st.rerun()

    st.divider()

    st.markdown("""
    <script>
    function styleOddButtons() {
        document.querySelectorAll('button').forEach(btn => {
            const txt = btn.innerText.trim();
            if (txt === 'Clear inputs') {
                btn.style.background = '#FAEEDA';
                btn.style.border = '1px solid #EF9F27';
                btn.style.color = '#633806';
                btn.style.fontWeight = '500';
            }
            if (txt === '✓ Accept' || txt === '+ Add to Odd Size List' || txt === '✓ Use this size') {
                btn.style.background = 'white';
                btn.style.border = '1.5px solid #1D9E75';
                btn.style.color = '#085041';
                btn.style.fontWeight = '500';
            }
            if (txt === 'Override size') {
                btn.style.border = '0.5px solid rgba(8,80,65,0.4)';
                btn.style.color = '#085041';
            }
        });
    }
    // Run on load and on DOM changes
    styleOddButtons();
    new MutationObserver(styleOddButtons).observe(document.body, {childList:true, subtree:true});
    </script>
    """, unsafe_allow_html=True)

    # ── Derive suggest values ─────────────────────────────────
    _has_dims = st.session_state.odd_cthk and st.session_state.odd_cwid
    if _has_dims:
        _ctu = st.session_state.odd_ctu; _cwu = st.session_state.odd_cwu
        _cthk_mm = float(st.session_state.odd_cthk) * 25 if _ctu == "inch" else float(st.session_state.odd_cthk)
        _cwid_mm = float(st.session_state.odd_cwid)  * 25 if _cwu == "inch" else float(st.session_state.odd_cwid)
        _cthk_mm, _cwid_mm = sorted([_cthk_mm, _cwid_mm])
        _compare_sawn = st.session_state.get("odd_dim_type", "Sawn") == "Sawn"
        _sug = suggest_quote_size(_cwid_mm, _cthk_mm, compare_sawn=_compare_sawn)
        _clen_val = st.session_state.odd_clen; _clu = st.session_state.odd_clu
        if _clen_val:
            if _clu == "ft":
                _sug_ft = math.ceil(float(_clen_val) * 2) / 2
            else:
                _sug_ft = m_to_half_ft(float(_clen_val))
        else:
            _sug_ft = 8
        if _sug:
            _sug_w, _sug_h, _sug_lbl, _, _ = _sug
            # In Sawn mode: show sawn dims prominently, planed in brackets
            # Sawn mode: show sawn dims + nominal inch label
            # Planed mode: show planed dims + nominal inch label
            # Both: clean single-dim display, no brackets
            _nom_inch_lbl = f"({mm_to_nominal_inch(_sug_w)}\" x {mm_to_nominal_inch(_sug_h)}\")"
            if _compare_sawn:
                _sug_display_lbl = f"{_sug_w} x {_sug_h}mm {_nom_inch_lbl}"
            else:
                # planed dims = sawn - 5mm per dim (from label)
                import re as _re
                _pm = _re.match(r'(\d+)\s*x\s*(\d+)mm', _sug_lbl)
                _pw, _ph = (int(_pm.group(1)), int(_pm.group(2))) if _pm else (_sug_w-5, _sug_h-5)
                _sug_display_lbl = f"{_pw} x {_ph}mm {_nom_inch_lbl}"
            _sug_full = f"{_sug_display_lbl} × {_sug_ft}ft ({ft_to_m_display(_sug_ft)}m)"
            _nom_w_s = mm_to_nominal_inch(_sug_w); _nom_h_s = mm_to_nominal_inch(_sug_h)
            _, _sug_pcs, _sug_price = calc_from_mm(_sug_w, _sug_h, _sug_ft, odd_rate, _nom_w_s, _nom_h_s)
        else:
            _sug_display_lbl = _sug_lbl = _sug_full = None; _sug_pcs = _sug_price = 0
    else:
        _sug = None; _sug_lbl = _sug_full = None; _sug_pcs = _sug_price = 0
        _cthk_mm = _cwid_mm = 0; _sug_w = _sug_h = 0; _sug_ft = 8

    _accepted = st.session_state.get("odd_accepted") and st.session_state.get("odd_acc_lbl")

    # ── Step 1: Customer dimensions ───────────────────────────
    _step1_done = bool(_has_dims and st.session_state.odd_clen)
    s1_num = "✓" if _step1_done else "1"
    s1_cls = "os-done" if _step1_done else "os-active"

    s1a, s1b = st.columns([0.08, 0.92])
    with s1a:
        st.markdown(f'<div class="os-num {s1_cls}" style="margin-top:20px">{s1_num}</div>', unsafe_allow_html=True)
    with s1b:
        st.markdown("<div style='font-size:11px;color:var(--color-text-secondary);margin-bottom:4px'>Paste or type customer dimensions</div>", unsafe_allow_html=True)
        p1, p2, p3, p4, p5, p6, p7 = st.columns([3.5, 0.7, 0.6, 1, 1, 1, 0.6])
        with p1: st.text_input("Paste", placeholder='e.g. 200×400×1600 or 8"x4"x20" or T200 W400 L1600', label_visibility="collapsed", key="odd_quickfill_inp")
        with p2:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            qf_btn = st.button("Fill ↓", use_container_width=True, key="odd_qf_btn")
        with p3: st.session_state.odd_ctu  = st.selectbox("Thk unit", ["mm","inch"], index=["mm","inch"].index(st.session_state.odd_ctu), key=f"odd_ctu_sel_{_fk}")
        with p4: st.session_state.odd_cthk = st.number_input("Thk", min_value=None, value=st.session_state.odd_cthk, placeholder="Thk", step=0.5, format="%.1f", key=f"odd_cthk_inp_{_fk}")
        with p5: st.session_state.odd_cwid = st.number_input("Wid (mm)", min_value=None, value=st.session_state.odd_cwid, placeholder="Wid", step=0.5, format="%.1f", key=f"odd_cwid_inp_{_fk}")
        with p6: st.session_state.odd_clen = st.number_input("Len",      min_value=None, value=st.session_state.odd_clen, placeholder="Len", step=0.1, format="%.2f", key=f"odd_clen_inp_{_fk}")
        with p7: st.session_state.odd_clu  = st.selectbox("Len unit", ["m","ft"], index=["m","ft"].index(st.session_state.odd_clu), key=f"odd_clu_sel_{_fk}")

    # Quick Fill parse
    _qf_val = st.session_state.get("odd_quickfill_inp", "").strip()
    if qf_btn and _qf_val:
        parsed = parse_dimension_string(_qf_val)
        if parsed:
            if parsed.get("t") is not None: st.session_state["odd_cthk"] = float(parsed["t"])
            if parsed.get("w") is not None: st.session_state["odd_cwid"] = float(parsed["w"])
            if parsed.get("l") is not None:
                _raw_m = round(float(parsed["l"]) / 1000, 3)
                st.session_state["odd_clen"] = snap_to_trade_length(_raw_m)
                st.session_state["odd_clu"]  = "m"
            st.session_state["odd_ctu"] = "mm"
            st.session_state["qf_fill_key"] += 1
            st.rerun()
        else:
            st.error("⚠️ Could not parse — try: 200×400×1600 or T200 W400 L1600")

    # Validation
    _val_errors = validate_odd_inputs(
        cthk_mm=_cthk_mm if _has_dims else None,
        cwid_mm=_cwid_mm if _has_dims else None,
        clen_val=float(st.session_state.odd_clen) if st.session_state.odd_clen else None,
        clu=st.session_state.odd_clu,
    )
    if _val_errors:
        for _e in _val_errors: st.error(_e)

    st.divider()

    # ── Step 2: Suggest ───────────────────────────────────────
    s2a, s2b = st.columns([0.08, 0.92])
    with s2a:
        _s2_cls = "os-done" if _accepted else ("os-active" if _step1_done and _sug and not _val_errors else "os-idle")
        _s2_num = "✓" if _accepted else "2"
        st.markdown(f'<div class="os-num {_s2_cls}" style="margin-top:8px">{_s2_num}</div>', unsafe_allow_html=True)
    with s2b:
        if _accepted:
            acc_full = st.session_state.odd_acc_full
            st.markdown(
                f'<div class="os-sug" style="margin-top:4px">'
                f'<span style="font-size:14px;font-weight:500;color:#085041">{acc_full}</span>'
                f'&nbsp;&nbsp;<span style="font-size:12px;color:#0F6E56">{st.session_state.odd_acc_pcs if "odd_acc_pcs" in st.session_state else ""} pcs · S${st.session_state.odd_acc_price if "odd_acc_price" in st.session_state else ""}/pc</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        elif _step1_done and _sug and not _val_errors:
            st.markdown(
                f'<div class="os-sug" style="margin-top:4px;display:flex;justify-content:space-between;align-items:center">'
                f'<div><div style="font-size:14px;font-weight:500;color:#085041">{_sug_full}</div>'
                f'<div style="font-size:11px;color:#0F6E56;margin-top:2px">'
                f'7200/{mm_to_nominal_inch(_sug_w)}/{mm_to_nominal_inch(_sug_h)}/{_sug_ft}ft = {_sug_pcs} pcs/ton → S${_sug_price}/pc</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            sc1, sc2 = st.columns([1, 4])
            with sc1:
                if st.button("✓ Accept", key="odd_accept_suggest", use_container_width=True):
                    st.session_state.odd_accepted    = True
                    st.session_state.odd_acc_w_mm    = float(_sug_w)
                    st.session_state.odd_acc_h_mm    = float(_sug_h)
                    st.session_state.odd_acc_ft      = _sug_ft
                    st.session_state.odd_acc_lbl     = _sug_lbl
                    st.session_state.odd_acc_full    = _sug_full
                    st.session_state.odd_acc_pcs     = _sug_pcs
                    st.session_state.odd_acc_price   = _sug_price
                    st.session_state.odd_qsize_label = _sug_lbl
                    st.session_state.odd_qft         = _sug_ft
                    st.rerun()
            with sc2:
                if st.button("Override size", key="odd_override"):
                    st.session_state.odd_accepted = False
                    st.session_state.odd_acc_lbl  = None
                    st.session_state.odd_qmode    = "free"
                    st.rerun()
        else:
            st.markdown('<div class="os-idle-box" style="margin-top:4px">Suggested quote size appears here after step 1</div>', unsafe_allow_html=True)

    # Override — free type
    if st.session_state.odd_qmode == "free" and not _accepted:
        st.caption("Enter your quote size manually:")
        fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 1])
        with fc1: st.session_state.odd_qthk_free = st.number_input("Thk (mm)", min_value=None, value=st.session_state.odd_qthk_free, placeholder="e.g. 130", step=0.5, format="%.1f", key="odd_qthk_free_inp")
        with fc2: st.session_state.odd_qwid_free = st.number_input("Wid (mm)", min_value=None, value=st.session_state.odd_qwid_free, placeholder="e.g. 180", step=0.5, format="%.1f", key="odd_qwid_free_inp")
        with fc3: st.session_state.odd_qlen_free = st.number_input("Len", min_value=None, value=st.session_state.odd_qlen_free, placeholder="e.g. 3.0", step=0.1, format="%.2f", key="odd_qlen_free_inp")
        with fc4: st.session_state.odd_qlu_free  = st.selectbox("Unit", ["m","ft"], index=["m","ft"].index(st.session_state.odd_qlu_free), key="odd_qlu_free_sel")

        qh_mm = float(st.session_state.odd_qthk_free) if st.session_state.odd_qthk_free else None
        qw_mm = float(st.session_state.odd_qwid_free) if st.session_state.odd_qwid_free else None
        _qlen_raw = float(st.session_state.odd_qlen_free) if st.session_state.odd_qlen_free else None
        _qlu = st.session_state.odd_qlu_free
        q_len_m_use = (_qlen_raw * 0.3048 if _qlu == "ft" else _qlen_raw) if _qlen_raw else None
        _qlen_display = f"{_qlen_raw}{_qlu}" if _qlen_raw else None
        quote_size_str = f"{st.session_state.odd_qthk_free}mm × {st.session_state.odd_qwid_free}mm × {_qlen_display}" if qh_mm and qw_mm and q_len_m_use else None

        if qw_mm and qh_mm and q_len_m_use:
            _ft_ov = m_to_half_ft(q_len_m_use) if _qlu == "m" else _qlen_raw
            _, _pcs_ov, _price_ov = calc_from_mm(qw_mm, qh_mm, _ft_ov, odd_rate)
            _line_ov = round(_price_ov * st.session_state.odd_qty, 2)
            st.caption(f"Preview: 7200/{mm_to_nominal_inch(qw_mm)}/{mm_to_nominal_inch(qh_mm)}/{_ft_ov}ft = {_pcs_ov} pcs → S${_price_ov}/pc")
            if st.button("✓ Use this size", key="odd_use_override"):
                _nom_ov_w = mm_to_nominal_inch(qw_mm); _nom_ov_h = mm_to_nominal_inch(qh_mm)
                raw_ov, pcs_ov, price_ov = calc_from_mm(qw_mm, qh_mm, _ft_ov, odd_rate, _nom_ov_w, _nom_ov_h)
                st.session_state.odd_accepted    = True
                st.session_state.odd_acc_w_mm    = qw_mm
                st.session_state.odd_acc_h_mm    = qh_mm
                st.session_state.odd_acc_ft      = _ft_ov
                st.session_state.odd_acc_lbl     = quote_size_str
                st.session_state.odd_acc_full    = f"{quote_size_str} × {_ft_ov}ft ({ft_to_m_display(_ft_ov)}m)"
                st.session_state.odd_acc_pcs     = pcs_ov
                st.session_state.odd_acc_price   = price_ov
                st.session_state.odd_qmode       = "dropdown"
                st.rerun()

    st.divider()

    # ── Step 3: Qty + Add ─────────────────────────────────────
    s3a, s3b = st.columns([0.08, 0.92])
    with s3a:
        _s3_cls = "os-active" if _accepted else "os-idle"
        st.markdown(f'<div class="os-num {_s3_cls}" style="margin-top:8px">3</div>', unsafe_allow_html=True)
    with s3b:
        if _accepted:
            acc_w   = st.session_state.odd_acc_w_mm
            acc_h   = st.session_state.odd_acc_h_mm
            acc_ft  = st.session_state.odd_acc_ft
            acc_lbl = st.session_state.odd_acc_lbl
            acc_full= st.session_state.odd_acc_full
            nom_w_a = mm_to_nominal_inch(acc_w); nom_h_a = mm_to_nominal_inch(acc_h)
            raw_a, pcs_fl_a, price_a = calc_from_mm(acc_w, acc_h, acc_ft, odd_rate, nom_w_a, nom_h_a)
            st.session_state.odd_qty = st.number_input("Qty (pcs)", min_value=1, value=st.session_state.odd_qty, step=1, key="odd_qty_acc")
            line_acc = round(price_a * st.session_state.odd_qty, 2)
            st.markdown(f'<div style="font-size:13px;color:#0F6E56;margin:4px 0">× S${price_a}/pc = <b style="color:#085041">S${line_acc:,.2f}</b></div>', unsafe_allow_html=True)
            if st.button("+ Add to Odd Size List", key="odd_add_accepted", use_container_width=True):
                _cthk_d = st.session_state.odd_cthk or acc_h
                _cwid_d = st.session_state.odd_cwid or acc_w
                _clen_d = st.session_state.odd_clen or ft_to_m_display(acc_ft)
                _clu_d  = st.session_state.odd_clu
                cust_size = f"{_cthk_d}mm × {_cwid_d}mm × {_clen_d}{_clu_d}"
                raw_a2, pcs_fl_a2, price_a2 = calc_from_mm(acc_w, acc_h, acc_ft, odd_rate, nom_w_a, nom_h_a)
                _dim_type = st.session_state.get("odd_dim_type", "Sawn")
                st.session_state.odd_items.append({
                    "species":     st.session_state.odd_sp,
                    "size":        acc_full,
                    "quote_size":  acc_full,
                    "cust_size":   cust_size,
                    "cust_thk_mm": _cthk_d,
                    "cust_wid_mm": _cwid_d,
                    "cust_len_m":  float(_clen_d) if _clu_d == "m" else None,
                    "w_mm": acc_w, "h_mm": acc_h, "ft": acc_ft,
                    "nom_w": nom_w_a, "nom_h": nom_h_a,
                    "rate":        odd_rate,
                    "pcs_per_ton": round(raw_a2, 4),
                    "pcs_floor":   pcs_fl_a2,
                    "price":       price_a2,
                    "qty":         st.session_state.odd_qty,
                    "line_total":  round(price_a2 * st.session_state.odd_qty, 2),
                    "small_qty":   st.session_state.odd_qty < SMALL_QTY,
                    "dim_type":    _dim_type,
                })
                # Reset for next entry
                for k, v in {"odd_cthk":None,"odd_cwid":None,"odd_clen":None,
                              "odd_ctu":"mm","odd_cwu":"mm","odd_clu":"m",
                              "odd_accepted":False,"odd_acc_lbl":None,"odd_acc_full":None,
                              "odd_acc_w_mm":None,"odd_acc_h_mm":None,"odd_acc_ft":None,
                              "odd_quickfill":"","odd_qmode":"dropdown",
                              "odd_qthk_free":None,"odd_qwid_free":None,"odd_qlen_free":None}.items():
                    st.session_state[k] = v
                st.session_state.qf_fill_key += 1
                st.session_state.odd_ready = False
                st.rerun()
        else:
            st.markdown('<div class="os-idle-box" style="margin-top:4px">Set qty &amp; add — available after accepting step 2</div>', unsafe_allow_html=True)

    if st.session_state.odd_items:
        st.divider()
        st.markdown(
            f'<div style="font-size:13px;color:var(--color-text-secondary);margin-bottom:6px">'
            f'Items in order: <span style="background:#1D9E75;color:white;font-size:12px;'
            f'padding:2px 8px;border-radius:99px;font-weight:600">{len(st.session_state.odd_items)}</span>'
            f'{cca_status_pill(st.session_state.odd_items)}</div>',
            unsafe_allow_html=True
        )
        _odd_sp_rates = {}
        for _oit in st.session_state.odd_items:
            _odd_sp_rates.setdefault(_oit["species"], set()).add(_oit["rate"])

        for i, item in enumerate(st.session_state.odd_items):
            _mixed = len(_odd_sp_rates.get(item["species"], set())) > 1
            _pcs_floor = item.get("pcs_floor", math.floor(float(item["pcs_per_ton"])))
            _odd_cca_on = item.get("cca", False)
            _ca, _cb, _cc, _cd = st.columns([7, 1, 1, 1])
            with _ca:
                render_item_card(
                    title=f'{item["species"]}',
                    pills=[
                        f'@S${item["rate"]:,}/ton' + (' ⚠' if _mixed else ''),
                        item.get("dim_type", "Sawn").lower(),
                    ],
                    detail_line=f'Customer: {item["cust_size"]} → Priced as: {item["quote_size"]}',
                    price_line=price_line_with_cca(item["price"], _odd_cca_on, cca_rate, item["qty"]),
                    warn=_mixed,
                    warn_note=f'Different rate from other {item["species"]} items in this quote' if _mixed else None,
                    footer_note=f'{_pcs_floor} pcs/ton',
                    badge_html=cca_badge_html(_odd_cca_on),
                )
            with _cb:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                if st.button("CCA", key=f"cca_odd_{i}",
                             help="Toggle CCA anti-termite / insect borer treatment",
                             use_container_width=True):
                    st.session_state.odd_items[i]["cca"] = not _odd_cca_on
                    st.session_state.odd_ready = False
                    st.rerun()
            with _cc:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                if st.button("↺", key=f"eo_{i}", help="Re-enter dimensions — restores this item to Step 1. Other items stay in the list.", use_container_width=True):
                    _it = st.session_state.odd_items.pop(i)
                    st.session_state["odd_cthk"]     = _it.get("cust_thk_mm")
                    st.session_state["odd_cwid"]     = _it.get("cust_wid_mm")
                    st.session_state["odd_clen"]     = _it.get("cust_len_m")
                    st.session_state["odd_clu"]      = "m"
                    st.session_state["odd_ctu"]      = "mm"
                    st.session_state["odd_sp"]       = _it["species"]
                    st.session_state["odd_accepted"] = False
                    st.session_state["odd_ready"]    = False
                    st.session_state["qf_fill_key"] += 1
                    st.rerun()
            with _cd:
                st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"do_{i}", use_container_width=True):
                    st.session_state.odd_items.pop(i); st.session_state.odd_ready=False; st.rerun()
        # Summary bar
        _odd_gt = sum(it["line_total"] for it in st.session_state.odd_items)
        _odd_gc = sum(round(it["line_total"]*0.85,2) for it in st.session_state.odd_items)
        _odd_gp = round(_odd_gt - _odd_gc, 2)
        _odd_gm = round(_odd_gp / _odd_gt * 100, 1) if _odd_gt > 0 else 0
        _n = len(st.session_state.odd_items)
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'background:var(--color-background-secondary);border-radius:var(--border-radius-md);'
            f'padding:10px 14px;margin-bottom:8px;font-size:13px">'
            f'<span style="color:var(--color-text-secondary)">{_n} item(s) · Margin {_odd_gm}%</span>'
            f'<span><b style="color:var(--color-text-primary)">S${_odd_gt:,.2f}</b>'
            f'<span style="font-size:11px;padding:1px 8px;border-radius:99px;'
            f'background:#E1F5EE;color:#0F6E56;margin-left:8px">Profit S${_odd_gp:,.2f}</span></span>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.divider()
        odd_valid_days = st.slider("Quote validity (days)", min_value=1, max_value=30,
            value=st.session_state.get("odd_valid_days", QUOTE_VALIDITY_DAYS), key="odd_valid_days")
        og1, og2 = st.columns([2, 1])
        with og1: gen_odd = st.button("GENERATE ODD SIZE QUOTE", type="primary", use_container_width=True)
        with og2:
            if st.button("Clear List", use_container_width=True):
                st.session_state.odd_items=[]; st.session_state.odd_ready=False; st.rerun()

        if gen_odd:
            odd_log=[]; odd_total=0; odd_cost=0
            for item in st.session_state.odd_items:
                _odd_item_cca = item.get("cca", False)
                _odd_combined_price = cca_combined_price(item["price"], _odd_item_cca, cca_rate)
                _odd_line_total = round(_odd_combined_price * item["qty"], 2)
                odd_total+=_odd_line_total
                cost_est=round(_odd_line_total*0.85,2); odd_cost+=cost_est
                profit=round(_odd_line_total-cost_est,2)
                margin_pct=round((profit/_odd_line_total*100),1) if _odd_line_total>0 else 0
                _odd_cca_badge_html = (
                    ' <span style="font-size:11px;padding:1px 8px;border-radius:99px;'
                    'background:#1D9E75;color:white;margin-left:6px">🧪 CCA</span>'
                    if _odd_item_cca else ""
                )
                _odd_price_rows = (
                    {
                        "Timber price/pc":   f"S${item['price']}",
                        "CCA rate/pc":       f"+ S${cca_rate:.2f} ({cca_colour})",
                        "Combined price/pc": f"S${_odd_combined_price}",
                    } if _odd_item_cca else
                    {"Price per piece": f"S${item['price']} (rounded up to nearest 10 cents)"}
                )
                odd_log.append({
                    "heading":f"{item['species']} (odd size){_odd_cca_badge_html}",
                    "rows":{
                        "Customer size":    item['cust_size'],
                        "Priced as":        item['quote_size'],
                        "Rate":             f"S${item['rate']}/ton",
                        "Pcs/ton (raw)":    str(item['pcs_per_ton']),
                        "Pcs used (floor)": str(item.get('pcs_floor',math.floor(float(item['pcs_per_ton'])))),
                        **_odd_price_rows,
                        "Qty":              f"{item['qty']} pcs",
                        "Line total":       f"S${_odd_line_total:,.2f}",
                    },
                    "profit_line":f"S${profit:,.2f}","margin_pct":f"{margin_pct}%","small_qty":item["small_qty"]
                })
            odd_total=round(odd_total,2); odd_cost=round(odd_cost,2)

            # Build grouped reply: group by (species, dim_type), sawn groups before planed
            from collections import defaultdict as _dd
            _groups = _dd(list)
            for item in st.session_state.odd_items:
                _dt = item.get("dim_type", "Sawn")
                _groups[(item["species"], _dt)].append(item)
            _group_order = sorted(_groups.keys(), key=lambda k: (0 if k[1]=="Sawn" else 1, k[0]))
            odd_reply = []; _odd_has_cca = False
            for _gi, _gkey in enumerate(_group_order):
                _sp, _dt = _gkey
                _items = _groups[_gkey]
                if _gi > 0:
                    odd_reply.append("")
                # Print group header only if at least one non-CCA item in group
                _non_cca_items = [_it for _it in _items if not _it.get("cca")]
                if _non_cca_items:
                    odd_reply.append(f"{_sp} timber {_dt.lower()}")
                for _it in _items:
                    if _it.get("cca"):
                        _odd_has_cca = True
                        _combined_odd = cca_combined_price(_it["price"], True, cca_rate)
                        _cca_line_total = round(_combined_odd * _it["qty"], 2)
                        odd_reply.append(
                            f"{_sp} timber {_dt.lower()} treated with anti-termite / insect borer treatment ({cca_colour})\n"
                            f"{_it['quote_size']} @ S${_combined_odd}/pcs x {_it['qty']} = S${_cca_line_total:,.2f}"
                        )
                    else:
                        odd_reply.append(
                            f"{_it['quote_size']}\n"
                            f"@ S${_it['price']}/pcs x {_it['qty']} = S${_it['line_total']:,.2f}"
                        )
            _odd_cca_note = "\n\nNote: After treatment, timber/plywood may be wet and may have some powder when dried." if _odd_has_cca else ""
            reply_text=build_reply(odd_reply,odd_total,is_timber=True,is_plywood=False,extra_note=_odd_cca_note,valid_days=odd_valid_days)
            st.session_state.odd_ready=True; st.session_state.odd_reply=reply_text
            st.session_state.odd_total=odd_total; st.session_state.odd_cost=odd_cost
            st.session_state.odd_nitem=len(odd_reply); st.session_state.odd_log=odd_log

        if st.session_state.odd_ready:
            render_quote_output("odd", save_type="Odd Size",
                show_metrics=False, show_staff_log=False,
                show_copy=True, show_clear=False, reply_height=300,
                file_prefix="odd_quote")
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
                    cost=effective_ply_cost(sel,thk); sell_def=PLY_SELL[sel][thk]
                    profit=round(sell_def-cost,2); margin=round((profit/sell_def*100),1) if sell_def>0 else 0
                    note=PLY_ACTUAL.get(sel,{}).get(thk,""); moq=PLY_MOQ.get(sel,{}).get(thk,1)
                    notes=[]
                    if note: notes.append(note)
                    if moq>1: notes.append(f"MOQ {moq} sheets")
                    tbl_rows.append({"Thickness":f"{thk}mm","YC Cost":f"S${cost}","Sell Price":f"S${sell_def}",
                        "Profit":f"S${profit}","Margin":f"{margin}%","Notes":" · ".join(notes) if notes else "—"})
                render_table(tbl_rows)

        st.divider()
        render_customer_section("ply")
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
        p_cost_def=effective_ply_cost(p_grade,p_thk)
        note=PLY_ACTUAL.get(p_grade,{}).get(p_thk,""); moq=PLY_MOQ.get(p_grade,{}).get(p_thk,1)

        # Tiered pricing (e.g. Birch Plywood): the default sell price depends on
        # qty, so peek at the qty widget's current value (persisted in session_state
        # from the previous rerun) before drawing the price field below.
        _cur_qty_guess = max(int(st.session_state.get("ply_qty_inp", 1)), 1)
        _tier_price = get_tiered_sell_price(p_grade, p_thk, _cur_qty_guess)
        _tier_bucket = ""
        if _tier_price is not None:
            p_sell_def = _tier_price
            _tier_info = PLY_SELL_TIERS[p_grade][p_thk]
            _tier_bucket = "hi" if _cur_qty_guess >= _tier_info["moq_threshold"] else "lo"

        if note: st.caption(f"ℹ️ {note}")
        if moq>1: st.caption(f"⚠️ MOQ: minimum {moq} sheets for this item")
        if _tier_price is not None:
            _ti = PLY_SELL_TIERS[p_grade][p_thk]
            st.caption(f"💲 Tiered pricing: S${_ti['sell_high_qty']}/sheet for {_ti['moq_threshold']}+ sheets, "
                       f"S${_ti['sell_low_qty']}/sheet for under {_ti['moq_threshold']} sheets")
        profit_preview=round(p_sell_def-p_cost_def,2)
        margin_preview=round((profit_preview/p_sell_def*100),1) if p_sell_def>0 else 0

        fa1,fa2,fa3,fa4=st.columns([2,1,1,1])
        with fa1:
            p_sell_key=f"ply_sell_{p_grade}_{p_thk}_{_tier_bucket}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            p_sell_f=st.number_input("Selling Price (S$/sheet)",min_value=0.0,value=float(p_sell_def),step=0.5,format="%.2f",key=p_sell_key)
        with fa2: p_qty_f=st.number_input("Qty (sheets)",min_value=1,value=1,step=1,key="ply_qty_inp")
        with fa3: st.markdown(f"<br><small>Default profit:<br>S${profit_preview}/sheet ({margin_preview}%)</small>",unsafe_allow_html=True)
        with fa4: st.markdown("<br>",unsafe_allow_html=True); add_ply=st.button("+ Add Plywood",type="primary",use_container_width=True,key="ply_add_btn")

        if p_sell_def==0.0: st.warning("⚠️ Selling price is S$0.00 — check price table.")
        if p_cost_def==0.0: st.caption("⚠️ Cost price not yet set for this item — profit/margin shown will be inaccurate until updated.")

        with st.expander(f"✏️ Update cost price for {p_grade} {p_thk}mm", expanded=False):
            _new_cost_key=f"newcost_{p_grade}_{p_thk}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            nc1, nc2 = st.columns([2,1])
            with nc1:
                new_cost_val = st.number_input("New cost price (S$/sheet)", min_value=0.0,
                    value=float(p_cost_def), step=0.5, format="%.2f", key=_new_cost_key)
            with nc2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Save cost price", key=f"savecost_{_new_cost_key}", use_container_width=True):
                    if update_ply_cost(p_grade, p_thk, new_cost_val):
                        st.success(f"✅ Cost updated: S${p_cost_def:.2f} → S${new_cost_val:.2f}")
                        st.rerun()
                    else:
                        st.error("❌ Could not save — check gist_id / github_token in Streamlit secrets.")
            _rlog = load_ply_rate_log()
            _rlog_here = [r for r in _rlog if r["grade"]==p_grade and r["thk"]==p_thk]
            if _rlog_here:
                st.caption("Rate history for this item:")
                render_table([
                    {"Date": f'{r["date"]} {r["time"]}', "Old cost": f'S${r["old_cost"]}', "New cost": f'S${r["new_cost"]}'}
                    for r in _rlog_here[:10]
                ])
            else:
                st.caption("No cost changes recorded yet for this item.")

        if add_ply:
            p_qty_f = max(int(st.session_state.get("ply_qty_inp", 1)), 1)
            # Recompute tier at the final qty in case it changed after the price field was drawn
            _final_tier = get_tiered_sell_price(p_grade, p_thk, p_qty_f)
            _final_sell_key = p_sell_key
            if _final_tier is not None:
                _ti2 = PLY_SELL_TIERS[p_grade][p_thk]
                _final_bucket = "hi" if p_qty_f >= _ti2["moq_threshold"] else "lo"
                _final_sell_key = f"ply_sell_{p_grade}_{p_thk}_{_final_bucket}".replace(" ","_").replace("/","_").replace("(","").replace(")","")
            p_sell_f = st.session_state.get(_final_sell_key, _final_tier if _final_tier is not None else p_sell_def)
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
            st.markdown(f"**Items in Order**{cca_status_pill(st.session_state.ply_items)}",
                        unsafe_allow_html=True)
            for i,item in enumerate(st.session_state.ply_items):
                _ply_cca_on = item.get("cca", False)
                _ply_profit_total = round(item['profit_ps']*item['actual_qty'],2)
                _ply_pills = [f"{item['thk']}mm"]
                if item["moq_flag"]:
                    _ply_pills.append("⚠️ MOQ")

                _ply_sell_r = item.get("sell_rounded", ceil_10cents(item["sell"]))
                render_item_card(
                    title=item['grade'],
                    pills=_ply_pills,
                    detail_line=f"Profit: S${_ply_profit_total:,.2f}",
                    price_line=price_line_with_cca(_ply_sell_r, _ply_cca_on, cca_rate,
                                                    item["actual_qty"], unit="sheet"),
                    badge_html=cca_badge_html(_ply_cca_on),
                )
                pc1, pc2, pc3 = st.columns([9, 1, 1])
                with pc2:
                    if st.button("CCA", key=f"cca_ply_{i}",
                                 help="Toggle CCA anti-termite / insect borer treatment"):
                        st.session_state.ply_items[i]["cca"] = not _ply_cca_on
                        st.session_state.ply_ready = False
                        st.rerun()
                with pc3:
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

            ply_valid_days = st.slider("Quote validity (days)", min_value=1, max_value=30,
                value=st.session_state.get("ply_valid_days", QUOTE_VALIDITY_DAYS), key="ply_valid_days")
            pg1,pg2=st.columns([2,1])
            with pg1: gen_ply=st.button("GENERATE PLYWOOD QUOTE",type="primary",use_container_width=True)
            with pg2:
                if st.button("Clear Plywood",use_container_width=True):
                    st.session_state.ply_items=[]; st.session_state.ply_ready=False; st.rerun()

            if gen_ply:
                ply_log=[]; ply_reply=[]; _ply_has_cca=False; _ply_grand_with_cca=ply_grand
                for item in st.session_state.ply_items:
                    _sell_r = item.get("sell_rounded", ceil_10cents(item["sell"]))
                    profit_total=round(item["profit_ps"]*item["actual_qty"],2)
                    margin_pct=round((item["profit_ps"]/_sell_r*100),1) if _sell_r>0 else 0
                    moq_note_txt=f"\n(MOQ {item['actual_qty']} sheets applied)" if item["moq_flag"] else ""
                    _ply_item_cca = item.get("cca", False)
                    _ply_cca_badge_html = (
                        ' <span style="font-size:11px;padding:1px 8px;border-radius:99px;'
                        'background:#1D9E75;color:white;margin-left:6px">🧪 CCA</span>'
                        if _ply_item_cca else ""
                    )
                    _ply_log_rows = {"Cost (YC)":f"S${item['cost']}/sheet","Selling (plywood)":f"S${_sell_r:.2f}/sheet (rounded up to nearest 10 cents)"}
                    _combined_ply = cca_combined_price(_sell_r, _ply_item_cca, cca_rate)
                    _ply_line_total = round(_combined_ply * item["actual_qty"], 2)
                    if _ply_item_cca:
                        _ply_log_rows["CCA rate/sheet"]       = f"+ S${cca_rate:.2f} ({cca_colour})"
                        _ply_log_rows["Combined price/sheet"] = f"S${_combined_ply:.2f}"
                    _ply_log_rows["Qty"]        = f"{item['actual_qty']} sheets"
                    _ply_log_rows["Line total"] = f"S${_ply_line_total:,.2f}"
                    ply_log.append({
                        "heading":f"{item['grade']} {item['thk']}mm{_ply_cca_badge_html}",
                        "rows":_ply_log_rows,
                        "profit_line":f"S${profit_total:,.2f}","margin_pct":f"{margin_pct}%","small_qty":False,
                        "moq_flag":item["moq_flag"],"moq_note":f"min {item['actual_qty']} sheets (requested {item['qty']})"
                    })
                    if _ply_item_cca:
                        _ply_has_cca = True
                        _ply_grand_with_cca += (_ply_line_total - item["line_total"])
                        ply_reply.append(
                            f"{item['grade']} plywood with anti-termite / insect borer treatment ({cca_colour})\n"
                            f"{item['thk']}mm x 1.22m x 2.44m @ S${_combined_ply:.2f}/sheet x {item['actual_qty']} = S${_ply_line_total:,.2f}{moq_note_txt}"
                        )
                    else:
                        cl=f"{item['grade']} plywood {item['thk']}mm x 1.22m x 2.44m @ S${_sell_r:.2f}/sheet x {item['actual_qty']} = S${_ply_line_total:,.2f}{moq_note_txt}"
                        ply_reply.append(cl)

                has_fr=any("Fire Retardant" in x["grade"] for x in st.session_state.ply_items)
                fr_note="\n* Note (Fire Retardant): Plywood may/will be wet & may/will have some powder when dried." if has_fr else ""
                _cca_ply_note = ("\n\nNote: After treatment, timber/plywood may be wet and may have some powder when dried." if _ply_has_cca else "")
                _combined_note = fr_note + _cca_ply_note
                reply_txt=build_reply(ply_reply,_ply_grand_with_cca,is_timber=False,is_plywood=True,extra_note=_combined_note,valid_days=ply_valid_days)
                st.session_state.ply_ready=True; st.session_state.ply_reply=reply_txt
                st.session_state.ply_total=_ply_grand_with_cca; st.session_state.ply_cost=ply_cost_total
                st.session_state.ply_nitem=len(ply_reply); st.session_state.ply_log=ply_log

            if st.session_state.ply_ready:
                render_quote_output("ply", save_type="Quote",
                    show_metrics=False, show_copy=True, show_clear=False,
                    reply_height=300, file_prefix="ply_quote")
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
# TAB 3.5 — COMBINED (Timber + Plywood in one reply)
# ============================================================
with tab_combined:
    st.markdown("#### Combine current Timber + Plywood items into one reply")
    st.caption("Pulls whatever is currently sitting in the Quote Builder and Plywood tabs. "
               "Nothing is removed from those tabs by generating here.")

    n_timber = len(st.session_state.order_items)
    n_ply = len(st.session_state.ply_items)

    cc1, cc2 = st.columns(2)
    with cc1: st.metric("Timber items (Quote Builder)", n_timber)
    with cc2: st.metric("Plywood items", n_ply)
    _comb_cca_pill = cca_status_pill(st.session_state.order_items + st.session_state.ply_items)
    if _comb_cca_pill:
        st.markdown(f'<div style="margin-top:-6px;margin-bottom:6px">{_comb_cca_pill}</div>',
                    unsafe_allow_html=True)

    if n_timber == 0 and n_ply == 0:
        st.info("Add items in the Quote Builder and/or Plywood tab first, then come back here to combine them.")
    else:
        comb_valid_days = st.slider("Quote validity (days)", min_value=1, max_value=30,
            value=st.session_state.get("comb_valid_days", QUOTE_VALIDITY_DAYS), key="comb_valid_days")
        if st.button("GENERATE COMBINED QUOTE", type="primary", use_container_width=True):
            combined_log = []; combined_reply = []
            combined_total = 0; combined_cost = 0
            combined_item_count = 0
            has_cca = False

            # ---- Timber section (same math as Quote Builder tab) ----
            if st.session_state.order_items:
                for item in st.session_state.order_items:
                    combined_item_count += 1
                    locked_rate = item["rate"]
                    locked_raw, _, locked_price = calc_from_mm(
                        item["w_mm"], item["h_mm"], item["ft"], locked_rate,
                        item.get("nom_w"), item.get("nom_h")
                    )
                    _item_cca = item.get("cca", False)
                    _combined_price = cca_combined_price(locked_price, _item_cca, cca_rate)
                    gt = round(_combined_price * item["qty"], 2)
                    combined_total += gt
                    cost_est = round(gt * 0.85, 2); combined_cost += cost_est
                    profit = round(gt - cost_est, 2)
                    margin_pct = round((profit / gt * 100), 1) if gt > 0 else 0
                    _cca_badge_html = (
                        ' <span style="font-size:11px;padding:1px 8px;border-radius:99px;'
                        'background:#1D9E75;color:white;margin-left:6px">🧪 CCA</span>'
                        if _item_cca else ""
                    )
                    _price_rows = (
                        {
                            "Timber price/pc":   f"S${locked_price}",
                            "CCA rate/pc":       f"+ S${cca_rate:.2f} ({cca_colour})",
                            "Combined price/pc": f"S${_combined_price}",
                        } if _item_cca else
                        {"Price per piece": f"S${locked_price}"}
                    )
                    combined_log.append({
                        "heading": f"{item['species']} timber · {item['size']}{_cca_badge_html}",
                        "rows": {
                            "Rate":            f"S${locked_rate:,}/ton",
                            "Pieces per ton":  str(round(locked_raw, 2)),
                            **_price_rows,
                            "Qty":             f"{item['qty']} pcs",
                            "Line total":      f"S${gt:,.2f}",
                        },
                        "profit_line": f"S${profit:,.2f}", "margin_pct": f"{margin_pct}%",
                        "small_qty": item["small_qty"]
                    })
                    if _item_cca:
                        has_cca = True
                        combined_reply.append(
                            f"{item['species']} timber planed treated with anti-termite / insect borer treatment ({cca_colour})\n"
                            f"{item['size']} @ S${_combined_price}/pcs x {item['qty']} = S${gt:,.2f}"
                        )
                    else:
                        combined_reply.append(
                            f"{item['species']} timber\n{item['size']} @ S${locked_price}/pcs x {item['qty']} = S${gt:,.2f}"
                        )

            # ---- Divider between sections (only if both present) ----
            if st.session_state.order_items and st.session_state.ply_items:
                combined_reply.append("-" * 32)

            # ---- Plywood section (same math as Plywood tab) ----
            has_fr = False
            if st.session_state.ply_items:
                for item in st.session_state.ply_items:
                    combined_item_count += 1
                    _sell_r = item.get("sell_rounded", ceil_10cents(item["sell"]))
                    profit_total = round(item["profit_ps"] * item["actual_qty"], 2)
                    margin_pct = round((item["profit_ps"] / _sell_r * 100), 1) if _sell_r > 0 else 0
                    moq_note_txt = f"\n(MOQ {item['actual_qty']} sheets applied)" if item["moq_flag"] else ""
                    _ply_item_cca = item.get("cca", False)
                    _ply_cca_badge_html = (
                        ' <span style="font-size:11px;padding:1px 8px;border-radius:99px;'
                        'background:#1D9E75;color:white;margin-left:6px">🧪 CCA</span>'
                        if _ply_item_cca else ""
                    )
                    _ply_log_rows = {"Cost (YC)": f"S${item['cost']}/sheet",
                                      "Selling (plywood)": f"S${_sell_r:.2f}/sheet (rounded up to nearest 10 cents)"}
                    _combined_ply = cca_combined_price(_sell_r, _ply_item_cca, cca_rate)
                    _ply_line_total = round(_combined_ply * item["actual_qty"], 2)
                    if _ply_item_cca:
                        has_cca = True
                        _ply_log_rows["CCA rate/sheet"] = f"+ S${cca_rate:.2f} ({cca_colour})"
                        _ply_log_rows["Combined price/sheet"] = f"S${_combined_ply:.2f}"
                    _ply_log_rows["Qty"] = f"{item['actual_qty']} sheets"
                    _ply_log_rows["Line total"] = f"S${_ply_line_total:,.2f}"
                    combined_total += _ply_line_total
                    combined_cost += item["cost"] * item["actual_qty"]
                    combined_log.append({
                        "heading": f"{item['grade']} {item['thk']}mm{_ply_cca_badge_html}",
                        "rows": _ply_log_rows,
                        "profit_line": f"S${profit_total:,.2f}", "margin_pct": f"{margin_pct}%", "small_qty": False,
                        "moq_flag": item["moq_flag"], "moq_note": f"min {item['actual_qty']} sheets (requested {item['qty']})"
                    })
                    if "Fire Retardant" in item["grade"]:
                        has_fr = True
                    if _ply_item_cca:
                        combined_reply.append(
                            f"{item['grade']} plywood with anti-termite / insect borer treatment ({cca_colour})\n"
                            f"{item['thk']}mm x 1.22m x 2.44m @ S${_combined_ply:.2f}/sheet x {item['actual_qty']} = S${_ply_line_total:,.2f}{moq_note_txt}"
                        )
                    else:
                        combined_reply.append(
                            f"{item['grade']} plywood {item['thk']}mm x 1.22m x 2.44m @ S${_sell_r:.2f}/sheet x {item['actual_qty']} = S${_ply_line_total:,.2f}{moq_note_txt}"
                        )

            combined_total = round(combined_total, 2); combined_cost = round(combined_cost, 2)
            fr_note = "\n* Note (Fire Retardant): Plywood may/will be wet & may/will have some powder when dried." if has_fr else ""
            cca_note = "\n\nNote: After treatment, timber/plywood may be wet and may have some powder when dried." if has_cca else ""
            reply_text = build_reply(
                combined_reply, combined_total,
                is_timber=bool(st.session_state.order_items),
                is_plywood=bool(st.session_state.ply_items),
                extra_note=fr_note + cca_note,
                valid_days=comb_valid_days
            )
            st.session_state.comb_ready = True; st.session_state.comb_reply = reply_text
            st.session_state.comb_total = combined_total; st.session_state.comb_cost = combined_cost
            st.session_state.comb_nitem = combined_item_count; st.session_state.comb_log = combined_log

        if st.session_state.get("comb_ready"):
            render_quote_output("comb", save_type="Combined", show_copy=True, show_clear=True,
                                 reply_height=350, file_prefix="combined_quote")

    st.divider()
    st.caption("Starting a brand new quote? This clears customer info and every item currently "
               "in Quote Builder, Odd Size, and Plywood, and resets species rates / CCA settings "
               "back to default.")
    if st.button("🔄 Clear All & Start New Quote", use_container_width=True, key="comb_full_reset"):
        reset_all()

# ============================================================
# TAB 4 — SUPPLIERS
# ============================================================
with tab_sup:
    st.markdown("""<div class="sup-header">
      <div class="sup-avatar">YC</div>
      <div><div class="sup-name">Ying Chuan Timber Co Pte Ltd</div>
      <div class="sup-sub">Supplier 1 &nbsp;·&nbsp; Updated May 2026</div></div>
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

    def _follow_up_row(_q, _detail_text):
        _fc1, _fc2 = st.columns([5, 1])
        with _fc1:
            st.markdown(
                f"&nbsp;&nbsp;• {_q.get('customer','—')} — {_detail_text}"
                f"{tag_badges_markdown(_q.get('tags', []))}"
            )
        with _fc2:
            if st.button("🔗 Follow up", key=f"followup_{_q.get('id','')}",
                          use_container_width=True):
                st.session_state.hist_search_val = _q.get("customer", "")
                st.session_state.hist_search_ver += 1
                st.rerun()

    _expired_list = st.session_state.get("expiry_banner_list", [])
    if _expired_list:
        _n_expired = len(_expired_list)
        st.error(f"❌ {_n_expired} quote{'s' if _n_expired != 1 else ''} expired this week — needs follow-up")
        for _q in _expired_list:
            _vu = effective_valid_until(_q)
            _follow_up_row(_q, f"expired {_vu.strftime('%d %b %Y')}")

    _soon_list = st.session_state.get("expiring_soon_list", [])
    if _soon_list:
        _n_soon = len(_soon_list)
        st.warning(
            f"⏰ {_n_soon} quote{'s' if _n_soon != 1 else ''} expiring soon (within "
            f"{EXPIRING_SOON_WORKING_DAYS} working days)"
        )
        for _q in _soon_list:
            _vu = effective_valid_until(_q)
            _days_left = (_vu.date() - now_sgt().date()).days
            _when = "today" if _days_left == 0 else f"in {_days_left} day{'s' if _days_left != 1 else ''}"
            _follow_up_row(_q, f"expires {_when} ({_vu.strftime('%d %b %Y')})")

    if _expired_list or _soon_list:
        st.divider()

    with st.form("hist_search_form",clear_on_submit=False):
        hs1,hs2,hs3=st.columns([4,1,1])
        with hs1:
            search=st.text_input("🔍 Search",value=st.session_state.hist_search_val,
                placeholder="Type customer name or mobile — press Enter or click Search",
                key=f"hist_search_inp_{st.session_state.hist_search_ver}",label_visibility="collapsed")
        with hs2: search_btn =st.form_submit_button("🔍 Search", use_container_width=True,type="primary")
        with hs3: refresh_btn=st.form_submit_button("🔄 Refresh",use_container_width=True)

    if refresh_btn:
        st.session_state.hist_search_val=""
        st.session_state.hist_search_ver += 1
        st.session_state.expiry_banner_checked = False
        st.session_state.expiring_soon_checked = False
        st.rerun()
    elif search_btn: st.session_state.hist_search_val=search

    with st.spinner("Loading history from cloud..."):
        history=load_history()

    if not history:
        st.info("No quotes saved yet. Generate a quote and click 'Save to History'.")
    else:
        active_search=st.session_state.hist_search_val.strip()
        name_matched=[q for q in history
            if active_search.lower() in q.get("customer","").lower()
            or active_search in q.get("mobile","")
        ] if active_search else history

        # ---- Type filter + Closed-only filter ----
        _type_options = ["All"] + sorted(set(q.get("type","Quote") for q in history))
        ft1, ft2 = st.columns([3,1])
        with ft1:
            type_filter = st.radio("Quote type", _type_options, horizontal=True,
                key="hist_type_filter", label_visibility="collapsed")
        with ft2:
            closed_only = st.checkbox("Closed only", key="hist_closed_only")

        filtered = name_matched
        if type_filter != "All":
            filtered = [q for q in filtered if q.get("type","Quote")==type_filter]
        if closed_only:
            filtered = [q for q in filtered if q.get("closed", False)]

        # ---- Overview metrics (based on full history, not the active filter) ----
        n_closed = sum(1 for q in history if q.get("closed", False))
        closed_value = sum(float(q.get("total",0)) for q in history if q.get("closed", False))
        closing_rate = round((n_closed / len(history) * 100), 1) if history else 0

        h1,h2,h3,h4=st.columns(4)
        with h1: st.metric("Total Quotes",     len(history))
        with h2: st.metric("Closed / Won",     n_closed)
        with h3: st.metric("Closing Rate",     f"{closing_rate}%")
        with h4: st.metric("Closed Value",     f"S${closed_value:,.2f}")
        h5,h6=st.columns(2)
        with h5: st.metric("All-time Revenue (quoted)", f"S${sum(float(q.get('total',0)) for q in history):,.2f}")
        with h6: st.metric("Unique Customers", len(set(q.get("customer","") for q in history if q.get("customer","—")!="—")))
        st.divider()

        # ---- Customer summary card: shown when the search narrows to exactly one customer name ----
        _unique_names = set(q.get("customer","—") for q in name_matched)
        if active_search and len(_unique_names) == 1 and name_matched:
            _cname = next(iter(_unique_names))
            _c_mobiles = sorted(set(q.get("mobile","—") for q in name_matched))
            _c_total = sum(float(q.get("total",0)) for q in name_matched)
            _c_closed = [q for q in name_matched if q.get("closed", False)]
            _c_closed_value = sum(float(q.get("total",0)) for q in _c_closed)
            _dates = [q.get("date","") for q in name_matched if q.get("date")]
            _date_range = f"{_dates[-1]} – {_dates[0]}" if len(_dates) > 1 else (_dates[0] if _dates else "—")
            _mobiles_note = f" ({', '.join(_c_mobiles)})" if len(_c_mobiles) > 1 else ""
            st.markdown(
                f'<div style="background:var(--color-background-secondary);border:0.5px solid var(--color-border-tertiary);'
                f'border-radius:var(--border-radius-md);padding:12px 16px;margin-bottom:14px">'
                f'<div style="font-size:13px;font-weight:600;margin-bottom:6px">Customer summary — {_cname}{_mobiles_note}</div>'
                f'<div style="font-size:13px;color:var(--color-text-secondary)">'
                f'{len(name_matched)} quote(s) &nbsp;·&nbsp; S${_c_total:,.2f} total quoted &nbsp;·&nbsp; '
                f'{len(_c_closed)} closed (S${_c_closed_value:,.2f}) &nbsp;·&nbsp; {_date_range}'
                f'</div></div>', unsafe_allow_html=True
            )

        if active_search or type_filter != "All" or closed_only:
            st.caption(f"{len(filtered)} quote(s) found")
        if not filtered:
            st.info("No quotes match your search/filter.")
        else:
            for i,q in enumerate(filtered):
                name=q.get("customer","—"); mobile=q.get("mobile","—")
                date=q.get("date","");      time=q.get("time","")
                total=float(q.get("total",0)); profit=float(q.get("profit",0)); margin=float(q.get("margin",0))
                text=q.get("text",""); qid=q.get("id",str(i)); qtype=q.get("type","Quote")
                is_closed = q.get("closed", False); closed_date = q.get("closed_date","")
                is_expired = quote_is_expired(q) and not is_closed
                type_icon={"Odd Size":"📐","Combined":"🔀"}.get(qtype,"📄")
                status_badge = ""
                if is_closed: status_badge = f" &nbsp;:violet-background[✅ Closed {closed_date}]"
                elif is_expired:
                    _vu = effective_valid_until(q)
                    _vu_disp = _vu.strftime("%d %b %Y") if _vu else "?"
                    status_badge = f" &nbsp;:orange-background[⏰ Expired (valid until {_vu_disp})]"
                else:
                    _vu = effective_valid_until(q)
                    if _vu:
                        _days_left = (_vu.date() - now_sgt().date()).days
                        _days_word = "day" if _days_left == 1 else "days"
                        status_badge = (f" &nbsp;:blue-background[Valid until "
                                        f"{_vu.strftime('%d %b %Y')} ({_days_left} {_days_word} left)]")
                label=f"{type_icon} [{qtype}]  {date} {time}  ·  {name}  ·  {mobile}  ·  SGD {total:,.2f}  ·  Profit SGD {profit:,.2f}  ({margin}%){status_badge}{tag_badges_markdown(q.get('tags', []))}"
                with st.expander(label):
                    st.text_area("Full quote",value=text,height=300,key=f"qt_{i}_{qid}")

                    _tag_keys = list(QUOTE_TAG_DEFS.keys())
                    _selected_tags = st.multiselect(
                        "Follow-up tags", options=_tag_keys,
                        default=[t for t in q.get("tags", []) if t in QUOTE_TAG_DEFS],
                        format_func=tag_option_label, key=f"tags_{i}_{qid}",
                    )
                    if _selected_tags != q.get("tags", []):
                        if set_quote_tags(qid, _selected_tags):
                            st.rerun()
                        else:
                            st.error("Could not save tags — try refreshing.")

                    hb1,hb2,hb3=st.columns(3)
                    with hb1:
                        clipboard_copy_button(text, key=f"hist_{i}_{qid}")
                    with hb2:
                        if is_closed:
                            st.button(f"✅ Closed on {closed_date}", key=f"closed_{i}_{qid}",
                                      disabled=True, use_container_width=True)
                        else:
                            if st.button("✅ Mark closed", key=f"markclosed_{i}_{qid}", use_container_width=True):
                                if mark_quote_closed(qid):
                                    st.session_state.expiry_banner_checked = False
                                    st.session_state.expiring_soon_checked = False
                                    st.success("Marked as closed."); st.rerun()
                                else: st.error("Could not update — try refreshing.")
                    with hb3:
                        if st.button("🗑️ Delete",key=f"dh_{i}_{qid}",use_container_width=True):
                            delete_quote(qid); st.success("Deleted."); st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Timber AI Assistant V33  · ALVIN  ")
