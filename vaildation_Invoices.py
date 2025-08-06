import json, streamlit as st
from PIL import Image
import fitz
from functools import partial

def val(x): return x.get("value","") if isinstance(x,dict) else x or ""
def conf(x): return float(x.get("confidence",0)) if isinstance(x,dict) else 0.0
def first(d,keys): return next((d[k] for k in d), "")

def set_row_edit_true(idx):
    st.session_state.row_editing[idx] = True

def set_row_edit_false(idx, pending_row_key, orig_row):
    st.session_state[pending_row_key] = dict(orig_row)
    st.session_state.row_editing[idx] = False

def parse(f):
    d = json.load(f)
    ext = d.get("extracted_data", d)
    sup = first(ext,["vendor_name","supplier","supplier_name","company","vendor"])
    num = ext.get("invoice_number")
    dat = ext.get("invoice_date")
    cust= ext.get("customer_details",{})
    tot = ext.get("totals_section") or ext.get("totals") or {}
    return dict(
        supplier_name =val(sup),  supplier_conf =conf(sup),
        invoice_number=val(num),  inv_num_conf  =conf(num),
        invoice_date  =val(dat),  inv_date_conf =conf(dat),
        customer_name =val(cust.get("name","")),  cust_conf     =conf(cust),
        customer_address=cust.get("address",""), cust_addr_conf =conf(cust),
        total = val(first(tot,["Total","Grand Total","total_amount","Total Amount",
                               "Invoice Amount","Net Total"])).replace("£","").replace("$","").strip(),
        total_conf=conf(tot),
        line_items = ext.get("items",[]),
        expected_confidence = 0.85
    )

def download(d):
    st.download_button("Download updated JSON",
        json.dumps(d,indent=4),"updated_invoice.json","application/json")

st.set_page_config("Invoice validator","📄",layout="wide")
st.title("Invoice Data Validation")

upl = st.file_uploader("Upload extracted-data JSON",["json"])
if not upl: st.stop()

if "last_upload" not in st.session_state or st.session_state["last_upload"] != upl:
    st.session_state.clear()
    st.session_state.update(parse(upl))
    st.session_state["last_upload"] = upl
    st.session_state.edited_fields = set()
    st.session_state.edited_items = [False] * len(st.session_state.line_items)

else:
    if "edited_fields" not in st.session_state:
        st.session_state.edited_fields = set()
    if "edited_items" not in st.session_state or len(st.session_state["edited_items"]) != len(st.session_state.line_items):
        st.session_state.edited_items = [False] * len(st.session_state.line_items)
fields = [
    ("Invoice Number", "invoice_number", "inv_num_conf"),
    ("Invoice Date",   "invoice_date",   "inv_date_conf"),
    ("Supplier Name",  "supplier_name",  "supplier_conf"),
    ("Customer Name",  "customer_name",  "cust_conf"),
    ("Customer Address","customer_address", "cust_addr_conf"),
    ("Total Amount",   "total",          "total_conf"),
]

def set_edit_true(key): st.session_state[key] = True
def set_edit_false(key): st.session_state[key] = False

for _, v_key, _ in fields:
    if f"{v_key}_editing" not in st.session_state:
        st.session_state[f"{v_key}_editing"] = False
    if f"{v_key}_pending" not in st.session_state:
        st.session_state[f"{v_key}_pending"] = st.session_state[v_key]

if "row_editing" not in st.session_state or len(st.session_state.get("row_editing", [])) != len(st.session_state.line_items):
    st.session_state.row_editing = [False] * len(st.session_state.line_items)

if "show_validated" not in st.session_state:
    st.session_state.show_validated = False

st.markdown("""
<style>
.inline-row {
    display: flex;
    align-items: center;
    gap: 0px;
}
.inline-row > div:first-child {
    font-weight: bold;
    margin: 0 !important;
    padding: 0 !important;
    white-space: nowrap;
}
.inline-row div[data-testid="stNumberInput"] {
    margin: 0 !important;
    padding: 0 !important;
}
.inline-row input {
    width: 70px !important;
    margin: 0 !important;
    padding: 2px 4px !important;
}
</style>
""", unsafe_allow_html=True)

cL, cM, cR = st.columns([1,2,1], gap="large")
with cM:
    st.markdown("<div class='inline-row'><div>Expected confidence</div></div>", unsafe_allow_html=True)
    thr = st.number_input("Expected confidence", 0.0, 1.0,
        st.session_state.expected_confidence, 0.01,
        key="expected_confidence", label_visibility="collapsed")

left, right = st.columns([3,2], gap="medium")
with left:
    doc = st.file_uploader("Preview invoice (image / PDF)",["png","jpg","jpeg","pdf"])
    if doc:
        if "image" in doc.type:
            st.image(Image.open(doc), use_column_width=True)
        else:
            st.image(fitz.open(stream=doc.read(),filetype="pdf")[0]
                .get_pixmap(matrix=fitz.Matrix(2,2)).tobytes("png"),
                use_column_width=True)


def draw_field(label, v_key, c_key):
    cf = st.session_state[c_key]
    edit = st.session_state[f"{v_key}_editing"]
    editable = (cf < thr) or edit
    bg_color = "#ff0000" if editable else "#00ff3c"
    text_color = "#fff" if editable else "#000"
    score_color = "#dc3545" if cf < thr else "#28a745"
    st.markdown(f"""
    <style>
    input[aria-label="{label}"],
    input[aria-label="{label}"]:disabled {{
        background:{bg_color} !important;
        color:{text_color} !important;
        -webkit-text-fill-color:{text_color} !important;
        font-weight:600 !important;
        opacity:1 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    # 4 columns: label | field | score | button
    labelcol, inputcol, scorecol, btncol = st.columns([2.1, 4, 1.2, 1.2], gap="small")
    with labelcol:
        st.markdown(f"<span style='font-weight:600'>{label}</span>", unsafe_allow_html=True)
    with inputcol:
        key = f"{v_key}_pending_input"
        if cf < thr:
            v = st.text_input(label, st.session_state[f"{v_key}_pending"], key=key, label_visibility='collapsed')
            if v != st.session_state[v_key]:
                st.session_state.edited_fields.add(v_key)
            st.session_state[f"{v_key}_pending"] = v
        elif edit:
            v = st.text_input(label, st.session_state[f"{v_key}_pending"], key=key, label_visibility='collapsed')
            if v != st.session_state[v_key]:
                st.session_state.edited_fields.add(v_key)
            st.session_state[f"{v_key}_pending"] = v
        else:
            st.text_input(label, st.session_state[v_key], key=f"{v_key}_input", disabled=True, label_visibility='collapsed')
    with scorecol:
        st.markdown(f'<div style="text-align:left; font-weight:bold; color:{score_color}; padding-left: 2px">{cf:.2f}</div>', unsafe_allow_html=True)
    with btncol:
        if cf >= thr:
            edit_key = f"{v_key}_editing"
            if not edit:
                st.button("Edit", key=f"{v_key}_edit_btn", on_click=set_edit_true, args=(edit_key,))
            else:
                st.button("Cancel", key=f"{v_key}_cancel_btn", on_click=set_edit_false, args=(edit_key,))
        else:
            st.markdown("")


with right:
    st.subheader("Extracted fields")
    for label, v_key, c_key in fields:
        draw_field(label, v_key, c_key)

# ---------- line items ----------
st.subheader("Line items")
fields_tag = [("desc", "description"), ("qty", "quantity"), ("unit", "unit_price"), ("total", "total_price")]
cols_hdr = st.columns([3,1,1,1,1,1])
for txt, col in zip(["Desc","Qty","Unit","Total","Conf","Edit"], cols_hdr):
    col.markdown(f"**{txt}**")

any_row_edit = False
for i, item in enumerate(st.session_state.line_items):
    cf = item.get("confidence", 0.0)
    edit = st.session_state.row_editing[i]
    any_row_edit = any_row_edit or edit
    pending_row_key = f"pending_row_{i}"
    if pending_row_key not in st.session_state:
        st.session_state[pending_row_key] = dict(item)
    editable = (cf < thr) or edit

    for j, (tag, field) in enumerate(fields_tag):
        bg = "#ff0000" if editable else "#00ff3c"
        txt = "#fff" if editable else "#000"
        aria = f"{tag}_{i}"
        st.markdown(f"""
        <style>
        input[aria-label="{aria}"],
        input[aria-label="{aria}"]:disabled {{
            background:{bg} !important;
            color:{txt} !important;
            -webkit-text-fill-color:{txt} !important;
            font-weight:600 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        if editable:
            val_now = cols_hdr[j].text_input(
                aria, st.session_state[pending_row_key][field],
                key=f"{aria}_pending_input", label_visibility="collapsed")
            # track if any cell differs from last committed value (after validation)
            if val_now != st.session_state.line_items[i][field]:
                st.session_state.edited_items[i] = True
            st.session_state[pending_row_key][field] = val_now
        else:
            cols_hdr[j].text_input(
                aria, st.session_state[pending_row_key][field],
                key=f"{aria}_input", disabled=True, label_visibility="collapsed")

    conf_color = "#dc3545" if cf < thr else "#28a745"
    cols_hdr[4].markdown(
        f"<span style='color:{conf_color}; font-weight:bold;'>{cf:.2f}</span>",
        unsafe_allow_html=True)
    # Only one edit/cancel per row in last col
    if cf >= thr:
        btn_label = "Cancel" if edit else "Edit"
        if not edit:
            cols_hdr[5].button(
                "Edit", key=f"row_{i}_edit_btn",
                on_click=partial(set_row_edit_true, i)
            )
        else:
            cols_hdr[5].button(
                "Cancel", key=f"row_{i}_cancel_btn",
                on_click=partial(set_row_edit_false, i, pending_row_key, st.session_state.line_items[i])
            )
    else:
        # For low-confidence rows, do NOT show any button. Editable always True.
        cols_hdr[5].markdown("")

# --------- VALIDATE and SHOW OUTPUT ---------
main_any_edit = any(st.session_state.get(f"{v_key}_editing", False) for _,v_key,_ in fields)
if main_any_edit or any_row_edit:
    st.markdown("---")
    cols = st.columns([5, 2, 5])  # Center layout
    with cols[1]:
        validate_clicked = st.button(":white_check_mark: Validate (Save All Edits)", key="validate_btn")
    if validate_clicked:
        for _, v_key, _ in fields:
            st.session_state[v_key] = st.session_state[f"{v_key}_pending"]
            st.session_state[f"{v_key}_editing"] = False
        for i in range(len(st.session_state.line_items)):
            st.session_state.line_items[i].update(st.session_state[f"pending_row_{i}"])
            st.session_state.row_editing[i] = False
        st.session_state.show_validated = True
        st.rerun()

if st.session_state.show_validated:
    st.markdown("----")
    st.subheader("Validated Data")
    for label, v_key, _ in fields:
        row = st.columns([1.3, 3])
        row[0].markdown(f"<div style='font-weight:600'>{label}:</div>", unsafe_allow_html=True)
        row[1].markdown(f"{st.session_state[v_key]}")
    st.markdown("**Line Items:**")
    if st.session_state.line_items:
        md = "| Description | Quantity | Unit Price | Total Price |\n"
        md += "|-------------|----------|------------|-------------|\n"
        for item in st.session_state["line_items"]:
            md += (
                f"| {item['description']} | {item['quantity']} |"
                f" {item['unit_price']} | {item['total_price']} |\n"
            )
        st.markdown(md)
    st.markdown("---")

# --------- Export, omitting confidence scores for edited fields/items ---------
edited_keys = set(st.session_state.edited_fields)
edited_item_indices = set(i for i, was_edited in enumerate(st.session_state.edited_items) if was_edited)


out = {}
out["supplier_name"] = st.session_state["supplier_name"]
if "supplier_name" not in edited_keys:
    out["supplier_conf"] = st.session_state.get("supplier_conf")
out["invoice_number"] = st.session_state["invoice_number"]
if "invoice_number" not in edited_keys:
    out["inv_num_conf"] = st.session_state.get("inv_num_conf")
out["invoice_date"] = st.session_state["invoice_date"]
if "invoice_date" not in edited_keys:
    out["inv_date_conf"] = st.session_state.get("inv_date_conf")
out["customer_name"] = st.session_state["customer_name"]
if "customer_name" not in edited_keys:
    out["cust_conf"] = st.session_state.get("cust_conf")
out["customer_address"] = st.session_state["customer_address"]
if "customer_address" not in edited_keys:
    out["cust_addr_conf"] = st.session_state.get("cust_addr_conf")
out["total"] = st.session_state["total"]
if "total" not in edited_keys:
    out["total_conf"] = st.session_state.get("total_conf")

final_items = []
for i, item in enumerate(st.session_state.line_items):
    it = {
        "description": item["description"],
        "quantity": item["quantity"],
        "unit_price": item["unit_price"],
        "total_price": item["total_price"]
    }
    if i not in edited_item_indices:
        it["confidence"] = item.get("confidence")
    final_items.append(it)
out["line_items"] = final_items

download(out)
