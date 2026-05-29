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

    with st.form("add_timber_form", clear_on_submit=True):
        fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 1, 1])
        with fc1: f_sp   = st.selectbox("Species", SPECIES, key="f_sp")
        with fc2: f_size = st.selectbox("Size (mm)", size_labels, key="f_size")
        with fc3: f_ft_label = st.selectbox("Length", ft_labels, key="f_ft")
        with fc4: f_qty  = st.number_input("Qty", min_value=None, value=None, placeholder="e.g. 1", step=1.0, format="%.0f", key="f_qty")
        with fc5:
            st.markdown("<br>", unsafe_allow_html=True)
            add_btn = st.form_submit_button("+ Add", use_container_width=True)

        if add_btn and f_size and f_ft_label:
            f_qty_int  = max(int(f_qty) if f_qty is not None else 1, 1)
            ft_val     = int(f_ft_label.split(" ")[0])
            w_mm, h_mm = lookup_size(f_size)
            rate       = species_rate[f_sp]
            raw, pcs, price = calc_from_mm(w_mm, h_mm, ft_val, rate)
            size_text  = f"{f_size} x {ft_val}ft"
            st.session_state.order_items.append({
                "species": f_sp, "size": size_text, "w_mm": w_mm, "h_mm": h_mm, "ft": ft_val,
                "price": price, "qty": f_qty_int, "line_total": round(price * f_qty_int, 2),
                "rate": rate, "pcs_per_ton": raw, "small_qty": f_qty_int < SMALL_QTY
            })
            st.session_state.q_ready = False
            st.rerun()

    if st.session_state.order_items:
        for i, item in enumerate(st.session_state.order_items):
            cur_rate = species_rate[item["species"]]
            raw, _, cur_price = calc_from_mm(item["w_mm"], item["h_mm"], item["ft"], cur_rate)
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
                cur_raw, _, cur_price = calc_from_mm(item["w_mm"], item["h_mm"], item["ft"], cur_rate)
                gt = round(cur_price * item["qty"], 2)
                grand_total += gt
                cost_est = round(gt * 0.85, 2); cost_total += cost_est
                profit = round(gt - cost_est, 2)
                margin_pct = round((profit / gt * 100), 1) if gt > 0 else 0
                log_items.append({
                    "heading": f"{item['species']} timber · {item['size']}",
                    "rows": {
                        "Rate":            f"S${cur_rate}/ton",
                        "Pieces per ton":  str(round(cur_raw, 2)),
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
                    q_thk_mm=float(qthk)*25.4; q_wid_mm=float(qwid)*25.4; quote_size=f'{qthk}" x {qwid}" x '
                else:
                    q_thk_mm=float(qthk); q_wid_mm=float(qwid); quote_size=f"{qthk}mm x {qwid}mm x "
                if qlu == "m":
                    q_len_m=float(qlen); quote_size+=f"{qlen}m"
                else:
                    q_len_m=float(qlen)/3.28084; quote_size+=f"{qlen}ft"
                vol=( q_wid_mm/1000)*(q_thk_mm/1000)*q_len_m
                raw=1/(vol*TIMBER_DENSITY_KG_M3/1000)
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
st.caption("Timber AI Assistant V27  ·  PLONY Industries  ·  Prices in SGD  ·  30 sizes · 6~22ft · AI & Cut-to-Size moved to separate apps")
