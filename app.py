# ============================================================
# Timber AI Assistant V26 — Full Enhanced Build
# Tabs: Quote Builder | Odd Size | Plywood | Suppliers | History | AI
# Cloud storage: GitHub Gist
# ============================================================

import streamlit as st
import pandas as pd
import math
import json
import requests
from datetime import datetime

st.set_page_config(layout="wide", page_title="Timber AI Assistant V26", page_icon="🪵")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.stButton button[kind="primary"] { background-color:#10b981!important; color:white!important; }
.stButton button[kind="primary"]:hover { background-color:#059669!important; }
.stTextArea textarea { font-family:'Calibri','Segoe UI',sans-serif!important; font-size:14px!important; line-height:1.7!important; }
.warn-box { background:#FAEEDA; color:#854F0B; font-size:13px; padding:8px 12px; border-radius:8px; margin:6px 0; }
.profit-line { font-size:13px; color:#0F6E56; font-weight:500; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GITHUB GIST HELPERS
# ============================================================
def gist_headers():
    token = st.secrets.get("github_token","")
    return {"Authorization":f"token {token}","Accept":"application/vnd.github.v3+json"}

def load_history():
    gist_id = st.secrets.get("gist_id","")
    if not gist_id: return []
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=gist_headers(), timeout=10)
        if r.status_code == 200:
            content = r.json()["files"]["timber_quotes.json"]["content"]
            return json.loads(content)
    except: pass
    return []

def save_history(history):
    gist_id = st.secrets.get("gist_id","")
    if not gist_id: return False
    try:
        r = requests.patch(f"https://api.github.com/gists/{gist_id}",
            headers=gist_headers(),
            json={"files":{"timber_quotes.json":{"content":json.dumps(history,indent=2)}}},
            timeout=10)
        return r.status_code == 200
    except: return False

def save_quote(customer, mobile, total, items, quote_text, cost_total=0):
    history = load_history()
    profit = round(total - cost_total, 2)
    margin = round((profit / total * 100), 1) if total > 0 else 0
    entry = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "date": datetime.now().strftime("%d %b %Y"),
        "time": datetime.now().strftime("%H:%M"),
        "customer": customer.strip() if customer.strip() else "—",
        "mobile": mobile.strip() if mobile.strip() else "—",
        "items": items,
        "total": total,
        "cost": cost_total,
        "profit": profit,
        "margin": margin,
        "text": quote_text
    }
    history.insert(0, entry)
    history = history[:200]
    return save_history(history)

def delete_quote(qid):
    history = load_history()
    save_history([q for q in history if q.get("id") != qid])

# ============================================================
# CONSTANTS & CALC (unchanged from V25)
# ============================================================
inch_to_mm = {1:20, 2:43, 3:70, 4:93, 5:117, 6:143, 7:168, 8:193, 9:218, 10:243, 12:293}

def mm_to_inch(mm):
    for inch, val in inch_to_mm.items():
        if abs(mm - val) <= 6: return inch
    return max(round(mm / 25.4), 1)

def inch_to_mm_val(inch):
    return inch_to_mm.get(inch, round(inch * 25.4))

def m_to_ft(m):
    if m <= 2.4: return 8
    elif m <= 3.0: return 10
    elif m <= 3.6: return 12
    elif m <= 4.2: return 14
    else: return round(m * 3.28084)

def calc(thk, wid, length, rate):
    raw = 7200 / (thk * wid * length)
    pcs_per_ton = round(raw, 3)
    pcs = max(math.floor(raw), 1)
    price = round(rate / pcs, 2)
    return pcs_per_ton, pcs, price

def is_keruing(species):
    return species in ["Mixed Keruing", "Pure Keruing"]

def build_reply(lines, total):
    out = list(lines)
    out.append(f"\nTotal : S${total:,.2f}")
    out.append("\nTolerances:")
    out.append("- Thickness/Width: +-1~2mm")
    out.append("- Length: +-25~50mm")
    out.append("\nDelivery / Self Collection:")
    out.append("30 Kranji Loop (Blk A) #04-05")
    out.append("TimMac @ Kranji S739570")
    return "\n".join(out)

# ============================================================
# PRICE DATA
# ============================================================
SPECIES = ["Kapur","Balau","Chengal","Mixed Keruing","Pure Keruing"]
SMALL_QTY_THRESHOLD = 10

# Plywood selling prices (default — editable in app)
PLY_SELL = {
    "MR China":         {2.2:3.25, 6:6.63, 9:9.36, 12:14.04, 15:19.0,  18:21.63},
    "WBP (TA)":         {6:11.31, 9:15.6,  12:18.46, 15:26.4, 18:27.5,  25:39.0},
    "BB/CC Furniture":  {3:5.72,  6:14.3,  9:16.75, 12:21.0,  15:26.4,  18:30.84, 25:44.04},
    "Casting Black China":   {12:18.84, 18:22.08},
    "Casting Black Vietnam": {12:19.625, 18:25.2},
    "Marine BS1088":    {9:36.0,  12:45.96, 15:52.0, 18:63.0,  25:84.0},
    "T2 Marine":        {6:21.0,  9:24.0,  12:31.2,  15:37.2,  18:43.2,  25:57.6},
    "Fire Retardant BS476": {3:40.0, 6:52.0, 9:74.0, 12:93.0, 15:102.0, 18:120.0, 25:150.0},
}

# Ying Chuan cost prices
PLY_COST = {
    "MR China":         {2.2:2.5,  6:5.1,   9:7.2,   12:10.8,  15:15.2,  18:17.3},
    "WBP (TA)":         {6:8.7,   9:12.0,  12:14.2,  15:22.0,  18:22.0,  25:32.5},
    "BB/CC Furniture":  {3:4.4,   6:11.0,  9:13.4,   12:16.8,  15:22.0,  18:25.7,  25:36.7},
    "Casting Black China":   {12:15.7, 18:18.4},
    "Casting Black Vietnam": {12:15.7, 18:21.0},
    "Marine BS1088":    {9:30.0,  12:38.3, 15:46.2,  18:56.7,  25:77.7},
    "T2 Marine":        {6:17.5,  9:20.0,  12:26.0,  15:31.0,  18:36.0,  25:48.0},
    "Fire Retardant BS476": {3:14.0, 6:26.0, 9:37.0, 12:49.0, 15:63.0, 18:70.0, 25:80.0},
}

# Thickness tolerance reference
PLY_TOLERANCE = {
    "MR China":        {"2.2mm": "±1.8mm actual", "3mm": "±2.0mm actual"},
    "BB/CC Furniture": {"3mm": "±2.2mm actual"},
    "WBP (TA)":        {"6mm": "±5.5mm actual"},
    "Marine BS1088":   {"9mm": "±8.5mm actual"},
}

PLY_MOQ = {"Fire Retardant BS476": {3: 10}, "MR China": {2.2: 10}}

# ============================================================
# SESSION STATE
# ============================================================
if "order_items" not in st.session_state:
    st.session_state.order_items = []
if "odd_items" not in st.session_state:
    st.session_state.odd_items = []
if "ply_items" not in st.session_state:
    st.session_state.ply_items = []
if "quote_saved" not in st.session_state:
    st.session_state.quote_saved = False

def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ============================================================
# HEADER
# ============================================================
c1, c2 = st.columns([5,1])
with c1:
    st.title("🪵 Timber AI Assistant V26")
    st.caption("Professional Quoting System · SGD · Cloud Edition")
with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("V26 Cloud")

# ============================================================
# RATES (top of page, always visible)
# ============================================================
with st.expander("⚙️ Timber Rates (SGD/ton) — click to edit", expanded=False):
    rc1,rc2,rc3,rc4,rc5 = st.columns(5)
    with rc1: kapur_rate  = st.number_input("Kapur",         value=3800, step=50, key="r_kapur")
    with rc2: balau_rate  = st.number_input("Balau",         value=5500, step=50, key="r_balau")
    with rc3: cheng_rate  = st.number_input("Chengal",       value=6000, step=50, key="r_cheng")
    with rc4: mkeruing_rate = st.number_input("Mixed Keruing", value=650, step=50, key="r_mker")
    with rc5: pkeruing_rate = st.number_input("Pure Keruing", value=1000, step=50, key="r_pker")

species_rate = {
    "Kapur": kapur_rate, "Balau": balau_rate, "Chengal": cheng_rate,
    "Mixed Keruing": mkeruing_rate, "Pure Keruing": pkeruing_rate
}

st.divider()

# ============================================================
# MAIN TABS
# ============================================================
tab_quote, tab_odd, tab_ply, tab_sup, tab_hist, tab_ai = st.tabs([
    "📋 Quote Builder",
    "📐 Odd Size",
    "🪵 Plywood",
    "🏭 Suppliers",
    "🕘 History",
    "🤖 AI (soon)"
])

# ============================================================
# TAB 1 — QUOTE BUILDER (Timber, form row style)
# ============================================================
with tab_quote:

    st.markdown("#### Customer Details")
    cd1, cd2 = st.columns(2)
    with cd1: cust_name   = st.text_input("Customer Name / Company", placeholder="e.g. ABC Construction Pte Ltd", key="cust_name")
    with cd2: cust_mobile = st.text_input("Mobile Number", placeholder="e.g. 9123 4567", key="cust_mobile")

    st.divider()
    st.subheader("Add Timber Item")

    # Form row — tab-friendly
    with st.form("add_timber_form", clear_on_submit=True):
        fc1,fc2,fc3,fc4,fc5,fc6,fc7,fc8,fc9 = st.columns([2,1,1,1,1,1,1,1,1])
        with fc1: f_species = st.selectbox("Species", SPECIES, key="f_sp")
        with fc2: f_thk     = st.number_input("Thickness", min_value=0.0, step=1.0, format="%.1f", key="f_thk")
        with fc3: f_tunit   = st.selectbox("Unit", ["mm","inch"], key="f_tu")
        with fc4: f_wid     = st.number_input("Width", min_value=0.0, step=1.0, format="%.1f", key="f_wid")
        with fc5: f_wunit   = st.selectbox("Unit ", ["mm","inch"], key="f_wu")
        with fc6: f_len     = st.number_input("Length", min_value=0.0, step=0.1, format="%.1f", key="f_len")
        with fc7: f_lunit   = st.selectbox("Unit  ", ["m","ft"], key="f_lu")
        with fc8: f_qty     = st.number_input("Qty", min_value=1, step=1, key="f_qty")
        with fc9:
            st.markdown("<br>", unsafe_allow_html=True)
            add_btn = st.form_submit_button("+ Add", use_container_width=True)

        if add_btn and f_thk > 0 and f_wid > 0 and f_len > 0:
            thk = mm_to_inch(f_thk) if f_tunit == "mm" else int(f_thk)
            wid = mm_to_inch(f_wid) if f_wunit == "mm" else int(f_wid)
            length = m_to_ft(f_len) if f_lunit == "m" else int(f_len)
            if length == 19: length = 20
            rate = species_rate[f_species]
            pcs_per_ton, pcs, price = calc(thk, wid, length, rate)

            # Cost estimate (timber — approx based on rate)
            cost_per_pc = round(rate / pcs / 1.15, 2)  # ~15% margin estimate for display

            if is_keruing(f_species):
                size_text = f'{thk}" x {wid}" x {length}ft'
                size_display = size_text
            else:
                mm_thk = inch_to_mm.get(thk, round(thk*25.4))
                mm_wid = inch_to_mm.get(wid, round(wid*25.4))
                size_text = f"{mm_thk}mm x {mm_wid}mm x {length}ft"
                size_display = size_text

            line_total = round(price * f_qty, 2)
            small_qty_flag = f_qty < SMALL_QTY_THRESHOLD

            st.session_state.order_items.append({
                "species": f_species,
                "size": size_display,
                "thk": thk, "wid": wid, "length": length,
                "price": price,
                "qty": f_qty,
                "line_total": line_total,
                "rate": rate,
                "pcs_per_ton": pcs_per_ton,
                "small_qty": small_qty_flag,
                "cost_per_pc": cost_per_pc
            })
            st.rerun()

    # Running order list
    if st.session_state.order_items:
        st.subheader("Order List")
        for i, item in enumerate(st.session_state.order_items):
            col_a, col_b, col_c, col_d = st.columns([3,2,1,1])
            with col_a:
                st.write(f"**{item['species']}**  {item['size']}")
                if item['small_qty']:
                    st.markdown(f'<div class="warn-box">⚠️ Small qty ({item["qty"]} pcs) — consider adjusting price</div>', unsafe_allow_html=True)
            with col_b:
                st.write(f"S${item['price']}/pc × {item['qty']} = **S${item['line_total']:,.2f}**")
            with col_c:
                if st.button("✏️ Edit", key=f"edit_t_{i}"):
                    st.session_state.order_items.pop(i)
                    st.rerun()
            with col_d:
                if st.button("🗑️", key=f"del_t_{i}"):
                    st.session_state.order_items.pop(i)
                    st.rerun()

        st.divider()

        # Generate
        col_gen, col_rst = st.columns([2,1])
        with col_gen:
            gen_quote = st.button("GENERATE QUOTE", type="primary", use_container_width=True)
        with col_rst:
            if st.button("RESET ALL", use_container_width=True):
                reset_all()

        if gen_quote:
            internal_view  = []
            customer_reply = []
            grand_total    = 0
            cost_total     = 0

            for item in st.session_state.order_items:
                line_total   = item["line_total"]
                grand_total += line_total
                cost_est     = round(item["cost_per_pc"] * item["qty"], 2)
                cost_total  += cost_est
                profit_pc    = round(item["price"] - item["cost_per_pc"], 2)
                margin_pct   = round((profit_pc / item["price"] * 100), 1) if item["price"] > 0 else 0

                flag = "⚠️ SMALL QTY — adjust price before sending\n" if item["small_qty"] else ""

                internal_view.append(
                    f"{item['species'].upper()} TIMBER\n{item['size']}\n\n"
                    f"Rate: S${item['rate']}/ton\n"
                    f"Pieces per ton: {item['pcs_per_ton']}\n"
                    f"Price per piece: S${item['price']}\n"
                    f"Quantity: {item['qty']} pcs\n"
                    f"Line total: S${line_total:,.2f}\n"
                    f"{flag}"
                    f"------------------------"
                )
                customer_reply.append(
                    f"{item['species']} timber\n{item['size']} @ S${item['price']}/pcs x {item['qty']} = S${line_total:,.2f}"
                )

            grand_total = round(grand_total, 2)
            cost_total  = round(cost_total, 2)
            profit      = round(grand_total - cost_total, 2)
            margin      = round((profit / grand_total * 100), 1) if grand_total > 0 else 0

            # Summary
            st.subheader("Quote Summary")
            m1,m2,m3,m4 = st.columns(4)
            with m1: st.metric("Items",        len(customer_reply))
            with m2: st.metric("Grand Total",  f"S${grand_total:,.2f}")
            with m3: st.metric("Est. Profit",  f"S${profit:,.2f}")
            with m4: st.metric("Est. Margin",  f"{margin}%")

            # Staff log
            st.subheader("Staff Calculation Log")
            st.text_area("", "\n".join(internal_view), height=250, key="staff_log_q")

            st.divider()

            # Customer reply — editable
            st.subheader("Customer Reply (edit before sending)")
            reply_text   = build_reply(customer_reply, grand_total)
            edited_reply = st.text_area("", reply_text, height=350, key="cust_reply_q")

            a1,a2,a3 = st.columns(3)
            with a1:
                st.download_button("📥 Download TXT", data=edited_reply,
                    file_name=f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True)
            with a2:
                if st.button("💾 Save to History", type="primary", use_container_width=True):
                    ok = save_quote(cust_name, cust_mobile, grand_total,
                                    len(customer_reply), edited_reply, cost_total)
                    if ok: st.success("✅ Saved to Quote History!")
                    else:  st.error("❌ Could not save — check Gist secrets.")
            with a3:
                st.download_button("📋 Copy as TXT", data=edited_reply,
                    file_name="quote_copy.txt", mime="text/plain",
                    use_container_width=True)
    else:
        st.info("Add items above to build your order list.")
        col_x, col_y = st.columns([2,1])
        with col_y:
            if st.button("RESET ALL", use_container_width=True):
                reset_all()


# ============================================================
# TAB 2 — ODD SIZE TIMBER
# ============================================================
with tab_odd:
    st.subheader("Odd Size Timber")
    st.caption("Customer requests a non-standard size. Price is calculated on your quote size. Customer reply shows their requested size.")

    with st.form("odd_size_form", clear_on_submit=True):
        st.markdown("**Species & Quantity**")
        oc1, oc2 = st.columns([3,1])
        with oc1: o_species = st.selectbox("Species", SPECIES, key="o_sp")
        with oc2: o_qty     = st.number_input("Qty (pcs)", min_value=1, step=1, key="o_qty")

        st.markdown("**Customer Requested Size**")
        cc1,cc2,cc3,cc4,cc5,cc6 = st.columns(6)
        with cc1: o_cthk   = st.number_input("Thickness", min_value=0.0, step=0.5, format="%.1f", key="o_cthk")
        with cc2: o_ctunit = st.selectbox("Unit", ["mm","inch"], key="o_ctu")
        with cc3: o_cwid   = st.number_input("Width", min_value=0.0, step=0.5, format="%.1f", key="o_cwid")
        with cc4: o_cwunit = st.selectbox("Unit ", ["mm","inch"], key="o_cwu")
        with cc5: o_clen   = st.number_input("Length", min_value=0.0, step=0.1, format="%.1f", key="o_clen")
        with cc6: o_clunit = st.selectbox("Unit  ", ["m","ft"], key="o_clu")

        st.markdown("**Your Quote Size (used for pricing)**")
        qc1,qc2,qc3,qc4,qc5,qc6 = st.columns(6)
        with qc1: o_qthk   = st.number_input("Thickness", min_value=0.0, step=0.5, format="%.1f", key="o_qthk")
        with qc2: o_qtunit = st.selectbox("Unit", ["mm","inch"], key="o_qtu")
        with qc3: o_qwid   = st.number_input("Width", min_value=0.0, step=0.5, format="%.1f", key="o_qwid")
        with qc4: o_qwunit = st.selectbox("Unit ", ["mm","inch"], key="o_qwu")
        with qc5: o_qlen   = st.number_input("Length", min_value=0.0, step=0.1, format="%.1f", key="o_qlen")
        with qc6: o_qlunit = st.selectbox("Unit  ", ["m","ft"], key="o_qlu")

        add_odd = st.form_submit_button("+ Add Odd Size Item", use_container_width=True)

        if add_odd and o_cthk > 0 and o_cwid > 0 and o_clen > 0 and o_qthk > 0 and o_qwid > 0 and o_qlen > 0:
            # Customer size display
            if o_ctunit == "inch":
                cust_size = f'{o_cthk}" x {o_cwid}" x {o_clen}{"ft" if o_clunit=="ft" else "m"}'
            else:
                cust_size = f"{o_cthk}mm x {o_cwid}mm x {o_clen}{o_clunit}"

            # Quote size for calculation
            q_thk    = mm_to_inch(o_qthk) if o_qtunit == "mm" else int(o_qthk)
            q_wid    = mm_to_inch(o_qwid) if o_qwunit == "mm" else int(o_qwid)
            q_length = m_to_ft(o_qlen)    if o_qlunit == "m"  else int(o_qlen)
            if q_length == 19: q_length = 20

            if o_qtunit == "inch":
                quote_size = f'{o_qthk}" x {o_qwid}" x {q_length}ft'
            else:
                mm_qthk = inch_to_mm.get(q_thk, round(q_thk*25.4))
                mm_qwid = inch_to_mm.get(q_wid, round(q_wid*25.4))
                quote_size = f"{mm_qthk}mm x {mm_qwid}mm x {q_length}ft"

            rate = species_rate[o_species]
            pcs_per_ton, pcs, price = calc(q_thk, q_wid, q_length, rate)
            line_total = round(price * o_qty, 2)
            small_qty_flag = o_qty < SMALL_QTY_THRESHOLD

            st.session_state.odd_items.append({
                "species":    o_species,
                "cust_size":  cust_size,
                "quote_size": quote_size,
                "price":      price,
                "qty":        o_qty,
                "line_total": line_total,
                "small_qty":  small_qty_flag,
                "rate":       rate,
                "pcs_per_ton": pcs_per_ton
            })
            st.rerun()

    # Odd size order list
    if st.session_state.odd_items:
        st.subheader("Odd Size Order List")
        for i, item in enumerate(st.session_state.odd_items):
            oa, ob, oc, od = st.columns([3,2,1,1])
            with oa:
                st.write(f"**{item['species']}**")
                st.caption(f"Customer: {item['cust_size']}  →  Priced as: {item['quote_size']}")
                if item["small_qty"]:
                    st.markdown(f'<div class="warn-box">⚠️ Small qty ({item["qty"]} pcs) — consider adjusting price</div>', unsafe_allow_html=True)
            with ob:
                st.write(f"S${item['price']}/pc × {item['qty']} = **S${item['line_total']:,.2f}**")
            with oc:
                if st.button("✏️", key=f"edit_o_{i}"):
                    st.session_state.odd_items.pop(i); st.rerun()
            with od:
                if st.button("🗑️", key=f"del_o_{i}"):
                    st.session_state.odd_items.pop(i); st.rerun()

        st.divider()

        col_gen2, col_rst2 = st.columns([2,1])
        with col_gen2:
            gen_odd = st.button("GENERATE ODD SIZE QUOTE", type="primary", use_container_width=True)
        with col_rst2:
            if st.button("Clear Odd Size", use_container_width=True):
                st.session_state.odd_items = []; st.rerun()

        if gen_odd:
            odd_internal = []
            odd_reply    = []
            odd_total    = 0

            for item in st.session_state.odd_items:
                odd_total += item["line_total"]
                flag = "⚠️ SMALL QTY — adjust price before sending\n" if item["small_qty"] else ""
                odd_internal.append(
                    f"{item['species'].upper()} TIMBER (ODD SIZE)\n"
                    f"Customer size: {item['cust_size']}\n"
                    f"Priced as: {item['quote_size']}\n\n"
                    f"Rate: S${item['rate']}/ton\n"
                    f"Pieces per ton: {item['pcs_per_ton']}\n"
                    f"Price per piece: S${item['price']}\n"
                    f"Quantity: {item['qty']} pcs\n"
                    f"Line total: S${item['line_total']:,.2f}\n"
                    f"{flag}"
                    f"------------------------"
                )
                # Customer reply shows THEIR requested size
                odd_reply.append(
                    f"{item['species']} timber\n{item['cust_size']} @ S${item['price']}/pcs x {item['qty']} = S${item['line_total']:,.2f}"
                )

            odd_total = round(odd_total, 2)

            st.subheader("Staff Calculation Log")
            st.text_area("", "\n".join(odd_internal), height=250, key="odd_log")

            st.divider()
            st.subheader("Customer Reply (edit before sending)")
            odd_reply_text   = build_reply(odd_reply, odd_total)
            odd_edited_reply = st.text_area("", odd_reply_text, height=300, key="odd_reply_out")

            od1, od2 = st.columns(2)
            with od1:
                st.download_button("📥 Download TXT", data=odd_edited_reply,
                    file_name=f"odd_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True)
            with od2:
                if st.button("💾 Save to History", type="primary", key="save_odd", use_container_width=True):
                    ok = save_quote(
                        st.session_state.get("cust_name",""),
                        st.session_state.get("cust_mobile",""),
                        odd_total, len(odd_reply), odd_edited_reply
                    )
                    if ok: st.success("✅ Saved!")
                    else:  st.error("❌ Could not save.")
    else:
        st.info("Add odd size items above.")


# ============================================================
# TAB 3 — PLYWOOD
# ============================================================
with tab_ply:
    ply_tab1, ply_tab2, ply_tab3 = st.tabs(["📦 Standard Plywood", "✂️ Cut-to-Size", "📏 Thickness Reference"])

    # ---- Standard Plywood ----
    with ply_tab1:
        st.subheader("Add Plywood Item")

        with st.form("add_ply_form", clear_on_submit=True):
            pc1, pc2, pc3 = st.columns([2,1,1])
            with pc1: p_grade = st.selectbox("Grade", list(PLY_SELL.keys()), key="p_gr")
            with pc2:
                available_thk = sorted(PLY_SELL.get(p_grade, {}).keys())
                p_thk = st.selectbox("Thickness (mm)", available_thk, key="p_thk")
            with pc3: p_qty = st.number_input("Qty (sheets)", min_value=1, step=1, key="p_qty")

            # Show sell price — editable
            default_sell = PLY_SELL.get(p_grade, {}).get(p_thk, 0.0)
            p_sell = st.number_input("Selling Price (S$/sheet)", value=float(default_sell),
                                      step=0.5, format="%.2f", key="p_sell")

            add_ply = st.form_submit_button("+ Add Plywood", use_container_width=True)

            if add_ply:
                cost      = PLY_COST.get(p_grade, {}).get(p_thk, 0.0)
                moq       = PLY_MOQ.get(p_grade, {}).get(p_thk, 1)
                actual_qty = max(p_qty, moq)
                moq_flag  = actual_qty > p_qty
                line_total = round(p_sell * actual_qty, 2)
                profit_ps  = round(p_sell - cost, 2)

                st.session_state.ply_items.append({
                    "grade":      p_grade,
                    "thk":        p_thk,
                    "sell":       p_sell,
                    "cost":       cost,
                    "qty":        p_qty,
                    "actual_qty": actual_qty,
                    "moq_flag":   moq_flag,
                    "line_total": line_total,
                    "profit_ps":  profit_ps,
                    "cut_to_size": False
                })
                st.rerun()

        if st.session_state.ply_items:
            st.subheader("Plywood Order List")
            ply_grand = 0
            ply_cost_total = 0

            for i, item in enumerate(st.session_state.ply_items):
                pa, pb, pc, pd = st.columns([3,2,1,1])
                with pa:
                    lbl = f"**{item['grade']}** {item['thk']}mm"
                    if item.get("cut_to_size"):
                        lbl += f" ✂️ {item.get('cut_dims','')}"
                    st.write(lbl)
                    if item["moq_flag"]:
                        st.markdown(f'<div class="warn-box">⚠️ MOQ {item["actual_qty"]} sheets applied (requested {item["qty"]})</div>', unsafe_allow_html=True)
                with pb:
                    st.write(f"S${item['sell']}/sheet × {item['actual_qty']} = **S${item['line_total']:,.2f}**")
                    profit_line = round(item['profit_ps'] * item['actual_qty'], 2)
                    st.markdown(f'<span class="profit-line">Profit: S${profit_line:,.2f}</span>', unsafe_allow_html=True)
                with pc:
                    if st.button("✏️", key=f"edit_p_{i}"):
                        st.session_state.ply_items.pop(i); st.rerun()
                with pd:
                    if st.button("🗑️", key=f"del_p_{i}"):
                        st.session_state.ply_items.pop(i); st.rerun()

                ply_grand      += item["line_total"]
                ply_cost_total += item["cost"] * item["actual_qty"]

            ply_grand      = round(ply_grand, 2)
            ply_cost_total = round(ply_cost_total, 2)
            ply_profit     = round(ply_grand - ply_cost_total, 2)
            ply_margin     = round((ply_profit / ply_grand * 100), 1) if ply_grand > 0 else 0

            st.divider()
            pm1,pm2,pm3 = st.columns(3)
            with pm1: st.metric("Plywood Total",  f"S${ply_grand:,.2f}")
            with pm2: st.metric("Profit",         f"S${ply_profit:,.2f}")
            with pm3: st.metric("Margin",         f"{ply_margin}%")

            pg1, pg2 = st.columns([2,1])
            with pg1:
                gen_ply = st.button("GENERATE PLYWOOD QUOTE", type="primary", use_container_width=True)
            with pg2:
                if st.button("Clear Plywood", use_container_width=True):
                    st.session_state.ply_items = []; st.rerun()

            if gen_ply:
                ply_internal = []
                ply_reply    = []
                for item in st.session_state.ply_items:
                    profit_ps = item["profit_ps"]
                    profit_total = round(profit_ps * item["actual_qty"], 2)
                    moq_note = f"\nNote: MOQ {item['actual_qty']} sheets applied" if item["moq_flag"] else ""
                    ply_internal.append(
                        f"{item['grade'].upper()} {item['thk']}mm\n\n"
                        f"Cost: S${item['cost']}/sheet\n"
                        f"Selling: S${item['sell']}/sheet\n"
                        f"Profit per sheet: S${profit_ps}\n"
                        f"Qty: {item['actual_qty']} sheets\n"
                        f"Line total: S${item['line_total']:,.2f}\n"
                        f"Line profit: S${profit_total:,.2f}\n"
                        f"{moq_note}\n"
                        f"------------------------"
                    )
                    cl = f"{item['grade']} plywood {item['thk']}mm @ S${item['sell']}/sheet x {item['actual_qty']} = S${item['line_total']:,.2f}"
                    if item["moq_flag"]: cl += f"\n(Min order {item['actual_qty']} sheets)"
                    ply_reply.append(cl)

                st.subheader("Staff Calculation Log")
                st.text_area("", "\n".join(ply_internal), height=250, key="ply_log")

                st.divider()
                st.subheader("Customer Reply (edit before sending)")
                ply_reply_text   = build_reply(ply_reply, ply_grand)
                ply_edited_reply = st.text_area("", ply_reply_text, height=300, key="ply_reply_out")

                pl1, pl2 = st.columns(2)
                with pl1:
                    st.download_button("📥 Download TXT", data=ply_edited_reply,
                        file_name=f"ply_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain", use_container_width=True)
                with pl2:
                    if st.button("💾 Save to History", type="primary", key="save_ply", use_container_width=True):
                        ok = save_quote(
                            st.session_state.get("cust_name",""),
                            st.session_state.get("cust_mobile",""),
                            ply_grand, len(ply_reply), ply_edited_reply, ply_cost_total
                        )
                        if ok: st.success("✅ Saved!")
                        else:  st.error("❌ Could not save.")
        else:
            st.info("Add plywood items above.")

    # ---- Cut-to-Size ----
    with ply_tab2:
        st.subheader("✂️ Cut-to-Size Plywood Calculator")
        st.caption("Calculate price for custom cut dimensions. Full sheet size is 4' x 8' (1220mm x 2440mm).")

        FULL_W = 1220
        FULL_L = 2440

        with st.form("cut_form", clear_on_submit=True):
            ct1, ct2 = st.columns(2)
            with ct1:
                c_grade = st.selectbox("Plywood Grade", list(PLY_SELL.keys()), key="c_gr")
                c_thk   = st.selectbox("Thickness (mm)", sorted(PLY_SELL.get(c_grade, {}).keys()), key="c_thk")
            with ct2:
                c_sell_default = PLY_SELL.get(c_grade, {}).get(c_thk, 0.0)
                c_sell  = st.number_input("Selling Price per full sheet (S$)", value=float(c_sell_default), step=0.5, format="%.2f", key="c_sell")

            st.markdown("**Cut dimensions required**")
            cd1, cd2, cd3 = st.columns(3)
            with cd1: c_w   = st.number_input("Cut Width (mm)",  min_value=1.0, value=800.0, step=10.0, key="c_w")
            with cd2: c_l   = st.number_input("Cut Length (mm)", min_value=1.0, value=800.0, step=10.0, key="c_l")
            with cd3: c_qty = st.number_input("Qty (cut pcs)",   min_value=1,   value=10,    step=1,    key="c_qty")

            calc_cut = st.form_submit_button("Calculate Cut-to-Size Price", use_container_width=True)

        if calc_cut:
            pcs_per_sheet_w = math.floor(FULL_W / c_w)
            pcs_per_sheet_l = math.floor(FULL_L / c_l)
            pcs_per_sheet   = pcs_per_sheet_w * pcs_per_sheet_l
            pcs_per_sheet   = max(pcs_per_sheet, 1)

            sheets_needed   = math.ceil(c_qty / pcs_per_sheet)
            price_per_cut   = round(c_sell / pcs_per_sheet, 2)
            total_cost      = round(price_per_cut * c_qty, 2)
            cost_price      = PLY_COST.get(c_grade, {}).get(c_thk, 0.0)
            cost_per_cut    = round(cost_price / pcs_per_sheet, 2)
            profit_per_cut  = round(price_per_cut - cost_per_cut, 2)
            total_profit    = round(profit_per_cut * c_qty, 2)
            margin_pct      = round((profit_per_cut / price_per_cut * 100), 1) if price_per_cut > 0 else 0

            st.subheader("Cut-to-Size Calculation")
            cr1,cr2,cr3,cr4 = st.columns(4)
            with cr1: st.metric("Pcs per sheet",    pcs_per_sheet)
            with cr2: st.metric("Sheets needed",    sheets_needed)
            with cr3: st.metric("Price per cut pc", f"S${price_per_cut}")
            with cr4: st.metric("Total",            f"S${total_cost:,.2f}")

            pm1,pm2,pm3 = st.columns(3)
            with pm1: st.metric("Cost per cut pc",   f"S${cost_per_cut}")
            with pm2: st.metric("Profit per cut pc", f"S${profit_per_cut}")
            with pm3: st.metric("Margin",            f"{margin_pct}%")

            cut_log = (
                f"CUT-TO-SIZE PLYWOOD\n"
                f"{c_grade} {c_thk}mm\n\n"
                f"Full sheet: {FULL_W}mm x {FULL_L}mm\n"
                f"Cut size: {int(c_w)}mm x {int(c_l)}mm\n"
                f"Pieces per sheet: {pcs_per_sheet} ({pcs_per_sheet_w}w x {pcs_per_sheet_l}l)\n"
                f"Sheets needed: {sheets_needed}\n"
                f"Full sheet price: S${c_sell}\n"
                f"Price per cut piece: S${price_per_cut}\n"
                f"Qty: {c_qty} pcs\n"
                f"Total: S${total_cost:,.2f}\n"
                f"Cost per cut pc: S${cost_per_cut}\n"
                f"Profit: S${total_profit:,.2f} ({margin_pct}%)\n"
                f"------------------------"
            )
            cut_reply = (
                f"{c_grade} plywood {c_thk}mm\n"
                f"Cut size {int(c_w)}mm x {int(c_l)}mm @ S${price_per_cut}/pc x {c_qty} = S${total_cost:,.2f}"
            )

            st.subheader("Staff Log")
            st.text_area("", cut_log, height=220, key="cut_log")
            st.subheader("Customer Reply (edit before sending)")
            cut_reply_full   = build_reply([cut_reply], total_cost)
            cut_edited       = st.text_area("", cut_reply_full, height=250, key="cut_reply_out")

            cx1, cx2 = st.columns(2)
            with cx1:
                st.download_button("📥 Download TXT", data=cut_edited,
                    file_name=f"cut_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain", use_container_width=True)
            with cx2:
                if st.button("💾 Save to History", type="primary", key="save_cut", use_container_width=True):
                    ok = save_quote(
                        st.session_state.get("cust_name",""),
                        st.session_state.get("cust_mobile",""),
                        total_cost, 1, cut_edited,
                        round(cost_per_cut * c_qty, 2)
                    )
                    if ok: st.success("✅ Saved!")
                    else:  st.error("❌ Could not save.")

    # ---- Thickness Reference ----
    with ply_tab3:
        st.subheader("📏 Plywood Thickness Tolerance Reference")
        st.caption("Nominal vs actual thickness by supplier — for quick reference when customers query thickness.")

        tol_data = {
            "Grade": [
                "MR China", "MR China",
                "BB/CC Furniture",
                "WBP (TA)",
                "Marine BS1088",
                "Fire Retardant BS476"
            ],
            "Nominal": ["2.2mm","3mm","3mm","6mm","9mm","3mm"],
            "Actual Thickness": [
                "±1.8mm","±2.0mm","±2.2mm","±5.5mm","±8.5mm","±2.8mm"
            ],
            "Supplier": [
                "Ying Chuan","Ying Chuan","Ying Chuan",
                "Ying Chuan","Ying Chuan","Ying Chuan"
            ],
            "Notes": [
                "China origin","China origin","T2 grade","TA grade",
                "BS1088 certified","BS476 Part 7 Class 1"
            ]
        }
        tol_df = pd.DataFrame(tol_data)
        st.dataframe(tol_df, use_container_width=True, hide_index=True)

        st.caption("You can add more rows as you discover tolerances from other suppliers.")


# ============================================================
# TAB 4 — SUPPLIERS
# ============================================================
with tab_sup:
    st.subheader("🏭 Supplier Rate Comparison")
    st.caption("Ying Chuan loaded as Supplier 1. Add more suppliers as you onboard them.")

    sup_tab1, sup_tab2 = st.tabs(["📊 Plywood Cost Comparison", "📈 Margin Summary"])

    with sup_tab1:
        st.markdown("**Ying Chuan — Cost Prices (SGD/sheet)**")
        grade_sel = st.selectbox("Select Grade to View", list(PLY_COST.keys()), key="sup_grade")

        if grade_sel in PLY_COST:
            rows = []
            for thk, cost in sorted(PLY_COST[grade_sel].items()):
                sell = PLY_SELL.get(grade_sel, {}).get(thk, 0)
                profit = round(sell - cost, 2)
                margin = round((profit / sell * 100), 1) if sell > 0 else 0
                rows.append({
                    "Thickness": f"{thk}mm",
                    "Ying Chuan Cost": f"S${cost}",
                    "Your Selling Price": f"S${sell}",
                    "Profit/sheet": f"S${profit}",
                    "Margin %": f"{margin}%"
                })
            sup_df = pd.DataFrame(rows)
            st.dataframe(sup_df, use_container_width=True, hide_index=True)

        st.info("More suppliers can be added in a future update once you onboard them.")

    with sup_tab2:
        st.markdown("**Overall Margin by Plywood Grade**")
        margin_rows = []
        for grade, thicknesses in PLY_SELL.items():
            costs  = PLY_COST.get(grade, {})
            sells  = list(thicknesses.values())
            cst    = [costs.get(t,0) for t in thicknesses.keys()]
            avg_sell   = round(sum(sells)/len(sells), 2) if sells else 0
            avg_cost   = round(sum(cst)/len(cst), 2)    if cst   else 0
            avg_profit = round(avg_sell - avg_cost, 2)
            avg_margin = round((avg_profit/avg_sell*100),1) if avg_sell > 0 else 0
            margin_rows.append({
                "Grade": grade,
                "Avg Cost": f"S${avg_cost}",
                "Avg Sell": f"S${avg_sell}",
                "Avg Profit": f"S${avg_profit}",
                "Avg Margin": f"{avg_margin}%"
            })
        margin_df = pd.DataFrame(margin_rows)
        st.dataframe(margin_df, use_container_width=True, hide_index=True)


# ============================================================
# TAB 5 — HISTORY
# ============================================================
with tab_hist:
    st.markdown("#### 🕘 Quote History")
    st.caption("Search by customer name or mobile. Tap any entry to read the full quote.")

    search = st.text_input("🔍 Search", placeholder="Type customer name or mobile...", key="hist_search")

    col_ref, _ = st.columns([1,4])
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    with st.spinner("Loading..."):
        history = load_history()

    if not history:
        st.info("No quotes saved yet. Generate a quote and click 'Save to History'.")
    else:
        if search.strip():
            filtered = [q for q in history
                        if search.lower() in q.get("customer","").lower()
                        or search.strip() in q.get("mobile","")]
            st.caption(f"{len(filtered)} quote(s) found for '{search}'")
        else:
            filtered = history

        h1,h2,h3,h4 = st.columns(4)
        with h1: st.metric("Total Quotes",     len(history))
        with h2:
            tv = sum(float(q.get("total",0)) for q in history)
            st.metric("All-time Revenue",   f"S${tv:,.2f}")
        with h3:
            tp = sum(float(q.get("profit",0)) for q in history)
            st.metric("All-time Profit",    f"S${tp:,.2f}")
        with h4:
            uniq = len(set(q.get("customer","") for q in history if q.get("customer","—")!="—"))
            st.metric("Unique Customers",   uniq)

        st.divider()

        if not filtered:
            st.info("No quotes match your search.")
        else:
            for i, q in enumerate(filtered):
                name   = q.get("customer","—")
                mobile = q.get("mobile","—")
                date   = q.get("date","")
                time   = q.get("time","")
                items  = q.get("items","")
                total  = float(q.get("total",0))
                profit = float(q.get("profit",0))
                margin = float(q.get("margin",0))
                text   = q.get("text","")
                qid    = q.get("id",str(i))

                label = f"📄  {date} {time}  ·  {name}  ·  {mobile}  ·  {items} item(s)  ·  S${total:,.2f}  ·  Profit S${profit:,.2f} ({margin}%)"

                with st.expander(label):
                    st.text_area("Full quote sent to customer", value=text, height=300, key=f"qt_{i}")
                    hb1, hb2 = st.columns(2)
                    with hb1:
                        st.download_button("📥 Download TXT", data=text,
                            file_name=f"quote_{date}_{name}.txt".replace(" ","_"),
                            mime="text/plain", key=f"dl_{i}", use_container_width=True)
                    with hb2:
                        if st.button("🗑️ Delete", key=f"del_h_{i}", use_container_width=True):
                            delete_quote(qid)
                            st.success("Deleted.")
                            st.rerun()


# ============================================================
# TAB 6 — AI ASSISTANT (placeholder)
# ============================================================
with tab_ai:
    st.markdown("#### 🤖 AI Assistant")
    st.info(
        "**Coming soon** — once your Anthropic API key is ready.\n\n"
        "You'll be able to describe what a customer needs in plain language "
        "and AI will fill in the order form automatically.\n\n"
        "For now, use the form row input in the Quote Builder tab."
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Timber AI Assistant V26  ·  Cloud Edition  ·  SGD  ·  TimMac @ Kranji")
