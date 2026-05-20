# ============================================================
# Timber AI Assistant V26
# Built from V25 base — Manual Table mode only
# Cloud-hosted on Streamlit Community Cloud
# Quote history saved to Google Sheets
# ============================================================

import streamlit as st
import pandas as pd
import math
import json
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Timber AI Assistant V26",
    page_icon="🪵"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
/* Primary green buttons */
.stButton button[kind="primary"] {
    background-color: #10b981 !important;
    color: white !important;
}
.stButton button[kind="primary"]:hover {
    background-color: #059669 !important;
}

/* Calibri-style text areas */
.stTextArea textarea {
    font-family: 'Calibri', 'Segoe UI', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}

/* Save button — blue */
div[data-testid="stButton"] button.save-btn {
    background-color: #3b82f6 !important;
    color: white !important;
}

/* History expand/collapse */
.logbook-header {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px;
    cursor: pointer;
    margin-bottom: 6px;
}
.logbook-header:hover { background: #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# GOOGLE SHEETS HELPER
# ============================================================
def get_sheet():
    """Connect to Google Sheets using Streamlit secrets."""
    try:
        from google.oauth2.service_account import Credentials
        import gspread

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet = client.open(st.secrets["sheet_name"]).sheet1
        return sheet
    except Exception as e:
        return None


def load_history_from_sheet():
    """Load all quote rows from Google Sheet."""
    sheet = get_sheet()
    if sheet is None:
        return []
    try:
        rows = sheet.get_all_records()
        return list(reversed(rows))  # newest first
    except:
        return []


def save_quote_to_sheet(customer_name, mobile, grand_total, item_count, quote_text):
    """Append one quote row to Google Sheet."""
    sheet = get_sheet()
    if sheet is None:
        st.warning("⚠️ Google Sheets not connected. Quote not saved to cloud.")
        return False
    try:
        # Check if header row exists
        existing = sheet.get_all_values()
        if not existing:
            sheet.append_row([
                "Date", "Time", "Customer Name", "Mobile",
                "Items", "Total (SGD)", "Quote Text"
            ])
        sheet.append_row([
            datetime.now().strftime("%d %b %Y"),
            datetime.now().strftime("%H:%M"),
            customer_name.strip() if customer_name.strip() else "—",
            mobile.strip() if mobile.strip() else "—",
            item_count,
            grand_total,
            quote_text
        ])
        return True
    except Exception as e:
        st.warning(f"⚠️ Could not save to Google Sheets: {e}")
        return False


# ============================================================
# CONSTANTS & CALC FUNCTIONS  (unchanged from V25)
# ============================================================
inch_to_mm = {1: 20, 2: 43, 3: 70, 4: 93, 6: 143, 8: 193}


def mm_to_inch(mm):
    for inch, val in inch_to_mm.items():
        if abs(mm - val) <= 5:
            return inch
    return max(round(mm / 25.4), 1)


def m_to_ft(m):
    if m <= 2.4:   return 8
    elif m <= 3.0: return 10
    elif m <= 3.6: return 12
    elif m <= 4.2: return 14
    else:          return round(m * 3.28084)


def calc(thk, wid, length, rate):
    raw = 7200 / (thk * wid * length)
    pcs_per_ton = round(raw, 3)
    pcs = max(math.floor(raw), 1)
    price = round(rate / pcs, 2)
    return pcs_per_ton, pcs, price


def is_keruing(species):
    return species in ["Mixed Keruing", "Pure Keruing"]


def build_customer_reply(customer_reply_lines, grand_total):
    lines = list(customer_reply_lines)
    lines.append(f"\nTotal : S${grand_total:,.2f}")
    lines.append("\nTolerances:")
    lines.append("- Thickness/Width: +-1~2mm")
    lines.append("- Length: +-25~50mm")
    lines.append("\nDelivery / Self Collection:")
    lines.append("30 Kranji Loop (Blk A) #04-05")
    lines.append("TimMac @ Kranji S739570")
    return "\n".join(lines)


# ============================================================
# SESSION STATE INIT
# ============================================================
if "timber_df" not in st.session_state:
    st.session_state.timber_df = pd.DataFrame([{
        "Species": "Kapur",
        "Thickness": None, "T Unit": "mm",
        "Width": None,     "W Unit": "mm",
        "Length": None,    "L Unit": "m",
        "Qty": None
    } for _ in range(5)])

if "plywood_df" not in st.session_state:
    st.session_state.plywood_df = pd.DataFrame([{
        "Type": "Marine", "Thickness": None, "Qty": None
    }])

if "last_quote_text" not in st.session_state:
    st.session_state.last_quote_text = ""

if "last_grand_total" not in st.session_state:
    st.session_state.last_grand_total = 0.0

if "last_item_count" not in st.session_state:
    st.session_state.last_item_count = 0

if "quote_saved" not in st.session_state:
    st.session_state.quote_saved = False


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


# ============================================================
# HEADER
# ============================================================
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.title("🪵 Timber AI Assistant V26")
    st.caption("Professional Quoting System · Prices in SGD · Cloud Edition")
with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("V26 Cloud")

# ============================================================
# RATES  (same layout as V25)
# ============================================================
st.subheader("Current Rates (SGD/ton)")
col1, col2, col3, col4, col5 = st.columns(5)
with col1: kapur_rate        = st.number_input("Kapur",        value=3800, step=50, key="kapur_rate")
with col2: balau_rate        = st.number_input("Balau",        value=5500, step=50, key="balau_rate")
with col3: chengal_rate      = st.number_input("Chengal",      value=6000, step=50, key="chengal_rate")
with col4: mixed_keruing_rate = st.number_input("Mixed Keruing", value=650, step=50, key="mixed_rate")
with col5: pure_keruing_rate  = st.number_input("Pure Keruing", value=1000, step=50, key="pure_rate")

species_rate = {
    "Kapur": kapur_rate,
    "Balau": balau_rate,
    "Chengal": chengal_rate,
    "Mixed Keruing": mixed_keruing_rate,
    "Pure Keruing": pure_keruing_rate
}

# ============================================================
# PLYWOOD PRICES  (same as V25)
# ============================================================
with st.expander("Plywood Prices (SGD/sheet)", expanded=False):
    ply_tab1, ply_tab2, ply_tab3 = st.tabs(["Marine", "Furniture", "MR"])

    with ply_tab1:
        ca, cb, _ = st.columns(3)
        with ca:
            marine_6mm  = st.number_input("Marine 6mm",  value=25.5,  step=0.5, key="marine_6",  format="%.2f")
            marine_9mm  = st.number_input("Marine 9mm",  value=36.0,  step=0.5, key="marine_9",  format="%.2f")
            marine_12mm = st.number_input("Marine 12mm", value=45.96, step=0.5, key="marine_12", format="%.2f")
        with cb:
            marine_15mm = st.number_input("Marine 15mm", value=52.0,  step=0.5, key="marine_15", format="%.2f")
            marine_18mm = st.number_input("Marine 18mm", value=63.0,  step=0.5, key="marine_18", format="%.2f")
            marine_25mm = st.number_input("Marine 25mm", value=84.0,  step=0.5, key="marine_25", format="%.2f")

    with ply_tab2:
        ca, cb, cc = st.columns(3)
        with ca:
            furn_3mm  = st.number_input("Furniture 3mm",  value=5.72,  step=0.5, key="furn_3",  format="%.2f")
            furn_6mm  = st.number_input("Furniture 6mm",  value=14.3,  step=0.5, key="furn_6",  format="%.2f")
            furn_9mm  = st.number_input("Furniture 9mm",  value=16.75, step=0.5, key="furn_9",  format="%.2f")
        with cb:
            furn_12mm = st.number_input("Furniture 12mm", value=21.0,  step=0.5, key="furn_12", format="%.2f")
            furn_15mm = st.number_input("Furniture 15mm", value=26.4,  step=0.5, key="furn_15", format="%.2f")
            furn_18mm = st.number_input("Furniture 18mm", value=30.84, step=0.5, key="furn_18", format="%.2f")
        with cc:
            furn_25mm = st.number_input("Furniture 25mm", value=44.04, step=0.5, key="furn_25", format="%.2f")

    with ply_tab3:
        ca, cb = st.columns(2)
        with ca:
            mr_3mm  = st.number_input("MR 3mm",  value=3.25,  step=0.5, key="mr_3",  format="%.2f")
            mr_6mm  = st.number_input("MR 6mm",  value=6.63,  step=0.5, key="mr_6",  format="%.2f")
            mr_9mm  = st.number_input("MR 9mm",  value=9.36,  step=0.5, key="mr_9",  format="%.2f")
        with cb:
            mr_12mm = st.number_input("MR 12mm", value=14.04, step=0.5, key="mr_12", format="%.2f")
            mr_15mm = st.number_input("MR 15mm", value=19.0,  step=0.5, key="mr_15", format="%.2f")
            mr_18mm = st.number_input("MR 18mm", value=21.63, step=0.5, key="mr_18", format="%.2f")

plywood_prices = {
    "Marine":    {6: marine_6mm, 9: marine_9mm, 12: marine_12mm, 15: marine_15mm, 18: marine_18mm, 25: marine_25mm},
    "Furniture": {3: furn_3mm, 6: furn_6mm, 9: furn_9mm, 12: furn_12mm, 15: furn_15mm, 18: furn_18mm, 25: furn_25mm},
    "MR":        {3: mr_3mm, 6: mr_6mm, 9: mr_9mm, 12: mr_12mm, 15: mr_15mm, 18: mr_18mm}
}

st.divider()

# ============================================================
# MAIN TABS
# ============================================================
tab_quote, tab_history, tab_ai = st.tabs([
    "📋  Quote Builder",
    "🕘  Quote History",
    "🤖  AI Assistant  (coming soon)"
])

# ============================================================
# TAB 1 — QUOTE BUILDER  (Manual Table only)
# ============================================================
with tab_quote:

    # Customer details
    st.markdown("#### Customer Details")
    cust_col1, cust_col2 = st.columns(2)
    with cust_col1:
        customer_name = st.text_input(
            "Customer Name / Company",
            placeholder="e.g. ABC Construction Pte Ltd",
            key="cust_name"
        )
    with cust_col2:
        customer_mobile = st.text_input(
            "Mobile Number",
            placeholder="e.g. 9123 4567",
            key="cust_mobile"
        )

    st.divider()

    # ---- Timber table ----
    with st.form(key="quote_form"):
        st.subheader("Timber Order")
        t_col1, t_col2 = st.columns([6, 1])
        with t_col2:
            if st.form_submit_button("Clear Timber"):
                st.session_state.timber_df = pd.DataFrame([{
                    "Species": "Kapur",
                    "Thickness": None, "T Unit": "mm",
                    "Width": None,     "W Unit": "mm",
                    "Length": None,    "L Unit": "m",
                    "Qty": None
                } for _ in range(5)])
                st.rerun()

        timber_table = st.data_editor(
            st.session_state.timber_df,
            num_rows="dynamic",
            use_container_width=True,
            key="timber_editor",
            column_config={
                "Species": st.column_config.SelectboxColumn(
                    options=["Kapur", "Balau", "Chengal", "Mixed Keruing", "Pure Keruing"]
                ),
                "T Unit": st.column_config.SelectboxColumn(options=["mm", "inch"], default="mm"),
                "W Unit": st.column_config.SelectboxColumn(options=["mm", "inch"], default="mm"),
                "L Unit": st.column_config.SelectboxColumn(options=["m", "ft"],   default="m")
            }
        )
        st.session_state.timber_df = timber_table

        # ---- Plywood table ----
        st.subheader("Plywood Order")
        p_col1, p_col2 = st.columns([6, 1])
        with p_col2:
            if st.form_submit_button("Clear Plywood"):
                st.session_state.plywood_df = pd.DataFrame([{
                    "Type": "Marine", "Thickness": None, "Qty": None
                }])
                st.rerun()

        plywood_table = st.data_editor(
            st.session_state.plywood_df,
            num_rows="dynamic",
            use_container_width=True,
            key="plywood_editor",
            column_config={
                "Type": st.column_config.SelectboxColumn(options=["Marine", "Furniture", "MR"])
            }
        )
        st.session_state.plywood_df = plywood_table

        # ---- Action buttons ----
        btn_col1, btn_col2 = st.columns([2, 1])
        with btn_col1:
            generate = st.form_submit_button(
                "GENERATE QUOTE", type="primary", use_container_width=True
            )
        with btn_col2:
            reset = st.form_submit_button("RESET ALL", use_container_width=True)

    if reset:
        reset_all()

    # ============================================================
    # GENERATE LOGIC  (V25 core, unchanged)
    # ============================================================
    if generate:
        internal_view  = []
        customer_reply = []
        grand_total    = 0
        errors         = []

        # ---- Process timber rows ----
        for idx, row in st.session_state.timber_df.iterrows():
            if pd.isna(row["Thickness"]) or pd.isna(row["Width"]) or \
               pd.isna(row["Length"])    or pd.isna(row["Qty"]):
                continue
            try:
                species = row["Species"]
                thk    = mm_to_inch(float(row["Thickness"])) if row["T Unit"] == "mm" else int(float(row["Thickness"]))
                wid    = mm_to_inch(float(row["Width"]))     if row["W Unit"] == "mm" else int(float(row["Width"]))
                length = m_to_ft(float(row["Length"]))       if row["L Unit"] == "m"  else int(float(row["Length"]))
                qty    = int(row["Qty"])
                if length == 19: length = 20

                rate = species_rate[species]
                pcs_per_ton, pcs, price = calc(thk, wid, length, rate)

                if is_keruing(species):
                    size_text = f'{thk}" x {wid}" x {length}ft'
                else:
                    mm_thk = inch_to_mm.get(thk, int(thk * 25.4))
                    mm_wid = inch_to_mm.get(wid, int(wid * 25.4))
                    size_text = f"{mm_thk}mm x {mm_wid}mm x {length}ft"

                line_total   = round(price * qty, 2)
                grand_total += line_total

                internal_view.append(
                    f"{species.upper()} TIMBER\n{size_text}\n\n"
                    f"Rate: S${rate}/ton\n"
                    f"Pieces per ton: {pcs_per_ton}\n"
                    f"Price per piece: S${price}\n"
                    f"Quantity: {qty} pcs\n"
                    f"Total: S${line_total}\n"
                    f"------------------------"
                )
                customer_reply.append(
                    f"{species} timber\n{size_text} @ S${price}/pcs x {qty} = S${line_total}"
                )
            except Exception as e:
                errors.append(f"Timber row {idx+1}: {str(e)}")

        # ---- Process plywood rows ----
        for idx, row in st.session_state.plywood_df.iterrows():
            if pd.isna(row["Thickness"]) or pd.isna(row["Qty"]):
                continue
            try:
                grade        = row["Type"]
                thk          = int(row["Thickness"])
                original_qty = int(row["Qty"])
                actual_qty   = original_qty
                moq_msg      = ""

                if grade == "MR" and thk == 3 and original_qty < 10:
                    actual_qty = 10
                    moq_msg    = "Note: MR 3mm minimum order quantity is 10pcs"

                if thk not in plywood_prices[grade]:
                    errors.append(f"Plywood row {idx+1}: {thk}mm not available for {grade}")
                    continue

                price        = plywood_prices[grade][thk]
                line_total   = round(price * actual_qty, 2)
                grand_total += line_total

                internal_view.append(
                    f"{grade.upper()} PLYWOOD\n{thk}mm\n\n"
                    f"Price per sheet: S${price}\n"
                    f"Customer requested: {original_qty} pcs\n"
                    f"Adjusted quantity: {actual_qty} pcs\n"
                    f"Total: S${line_total}\n"
                    f"{moq_msg}\n"
                    f"------------------------"
                )
                cl = f"{grade} plywood {thk}mm @ S${price}/pcs x {actual_qty} = S${line_total}"
                if moq_msg: cl += f"\n({moq_msg})"
                customer_reply.append(cl)

            except Exception as e:
                errors.append(f"Plywood row {idx+1}: {str(e)}")

        grand_total = round(grand_total, 2)

        # ---- Show errors ----
        for err in errors:
            st.warning(err)

        # ---- Display results ----
        if internal_view:

            # Summary metrics
            st.subheader("Quote Summary")
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Total Items", len(customer_reply))
            with m2: st.metric("Grand Total", f"S${grand_total:,.2f}")
            with m3: st.metric("Generated", datetime.now().strftime("%d %b %Y  %H:%M"))

            # Staff log
            st.subheader("Staff Calculation Log")
            st.text_area("", "\n".join(internal_view), height=280, key="staff_log")

            st.divider()

            # Customer reply — fully editable
            st.subheader("Customer Reply  (edit before sending)")
            reply_text = build_customer_reply(customer_reply, grand_total)

            # Store for saving
            st.session_state.last_quote_text  = reply_text
            st.session_state.last_grand_total = grand_total
            st.session_state.last_item_count  = len(customer_reply)
            st.session_state.quote_saved      = False

            edited_reply = st.text_area(
                "", reply_text, height=380, key="customer_reply_out"
            )

            # Action row
            act1, act2, act3 = st.columns(3)
            with act1:
                st.download_button(
                    "📥 Download TXT",
                    data=edited_reply,
                    file_name=f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with act2:
                if st.button("💾 Save to History", use_container_width=True, type="primary"):
                    ok = save_quote_to_sheet(
                        customer_name,
                        customer_mobile,
                        grand_total,
                        len(customer_reply),
                        edited_reply
                    )
                    if ok:
                        st.session_state.quote_saved = True
                        st.success("✅ Quote saved to Google Sheets!")
            with act3:
                if st.button("📋 Copy Text", use_container_width=True):
                    st.code(edited_reply, language=None)
                    st.info("Select all text above and copy (Ctrl+A then Ctrl+C)")

            if st.session_state.quote_saved:
                st.success("✅ Saved — visible in Quote History tab.")

        else:
            st.warning("No valid items found. Please fill in the order tables.")


# ============================================================
# TAB 2 — QUOTE HISTORY  (Logbook style)
# ============================================================
with tab_history:
    st.markdown("#### Quote History")
    st.caption("All quotes saved to your Google Sheet — searchable by customer name or mobile.")

    # Search bar
    search = st.text_input(
        "🔍 Search",
        placeholder="Type customer name or mobile number...",
        key="history_search"
    )

    # Load from Google Sheets
    with st.spinner("Loading history..."):
        history = load_history_from_sheet()

    if not history:
        st.info("No quotes saved yet, or Google Sheets not connected. Generate a quote and click 'Save to History'.")
    else:
        # Filter by search
        if search.strip():
            filtered = [
                q for q in history
                if search.lower() in str(q.get("Customer Name", "")).lower()
                or search.strip() in str(q.get("Mobile", ""))
            ]
        else:
            filtered = history

        # Summary stats
        s1, s2, s3 = st.columns(3)
        with s1: st.metric("Total Quotes", len(history))
        with s2:
            total_val = sum(float(q.get("Total (SGD)", 0)) for q in history)
            st.metric("All-time Value", f"S${total_val:,.2f}")
        with s3:
            customers = len(set(q.get("Customer Name", "") for q in history if q.get("Customer Name", "—") != "—"))
            st.metric("Unique Customers", customers)

        st.divider()

        if search.strip():
            st.caption(f"{len(filtered)} quote(s) found for '{search}'")

        if not filtered:
            st.info("No quotes match your search.")
        else:
            for i, q in enumerate(filtered):
                name   = q.get("Customer Name", "—")
                mobile = q.get("Mobile", "—")
                date   = q.get("Date", "")
                time   = q.get("Time", "")
                items  = q.get("Items", "")
                total  = q.get("Total (SGD)", 0)
                text   = q.get("Quote Text", "")

                label = f"📄  {date} {time}  ·  {name}  ·  {mobile}  ·  {items} item(s)  ·  S${float(total):,.2f}"

                with st.expander(label):
                    st.text_area(
                        "Full quote text",
                        value=text,
                        height=300,
                        key=f"hist_text_{i}"
                    )
                    h1, h2 = st.columns(2)
                    with h1:
                        st.download_button(
                            "📥 Download TXT",
                            data=text,
                            file_name=f"quote_{date}_{name}.txt".replace(" ", "_"),
                            mime="text/plain",
                            key=f"dl_{i}",
                            use_container_width=True
                        )
                    with h2:
                        if st.button("↩ Reload into Quote Builder", key=f"reload_{i}", use_container_width=True):
                            st.info("Switch to the Quote Builder tab and re-enter the items manually. "
                                    "AI-assisted reload coming in a future version.")


# ============================================================
# TAB 3 — AI ASSISTANT  (placeholder, ready for API key)
# ============================================================
with tab_ai:
    st.markdown("#### 🤖 AI Assistant")
    st.info(
        "AI-powered quote assistant coming soon.\n\n"
        "Once your Anthropic API key is set up, you'll be able to:\n"
        "- Describe what a customer needs in plain language\n"
        "- Let AI fill in the order table automatically\n"
        "- Handle messy WhatsApp-style messages\n\n"
        "For now, use the Manual Table in the Quote Builder tab."
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("Timber AI Assistant V26  ·  Cloud Edition  ·  Prices in SGD  ·  TimMac @ Kranji")
