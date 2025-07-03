# single rule based ui file 
import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Advanced Rule Engine", layout="wide")
st.title("🧠 Priority-Based Rule Engine")

if "rules" not in st.session_state:
    st.session_state.rules = []

# Upload CSV
st.subheader("📅 Upload Your CSV File")
uploaded_file = st.file_uploader("Upload CSV with Supplier, Amount, etc.", type=["csv"])
df = pd.DataFrame()
supplier_options = []
category_filter = "All"

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully!")
        st.dataframe(df, use_container_width=True)
        if "Supplier" in df.columns:
            supplier_options = sorted(df["Supplier"].dropna().unique().astype(str).tolist())
    except Exception as e:
        st.error(f"❌ Error loading CSV: {e}")

# Rule Builder
st.subheader("➕ Create Rule (Supplier + Amount Range + Logic)")
with st.form("rule_form"):
    supplier = st.selectbox("Select Supplier", ["--Select--"] + supplier_options) if supplier_options else st.text_input("Enter Supplier Name (case insensitive)")
    col1, col2 = st.columns(2)
    with col1:
        min_amount = st.number_input("Minimum Amount", step=1.0, key="min_amt")
    with col2:
        max_amount = st.number_input("Maximum Amount", step=1.0, key="max_amt")
    logic = st.radio("Apply Logic Between Conditions", ["AND", "OR"], horizontal=True)
    category_list = ["--Select--", "Stationery", "Consulting", "Training", "Maintenance", "Insurance", "Miscellaneous", "Travel", "Office Supplies", "Utilities", "Marketing", "IT Services"]
    category = st.selectbox("Select Category", category_list)
    submitted = st.form_submit_button("✅ Add Rule")
    if submitted:
        if supplier and supplier != "--Select--" and category != "--Select--" and min_amount <= max_amount:
            rule = {
                "supplier": supplier.strip().lower(),
                "min_amount": float(min_amount),
                "max_amount": float(max_amount),
                "logic": logic,
                "category": category
            }
            st.session_state.rules.append(rule)
            st.success("✅ Rule added!")
        else:
            st.warning("⚠️ Please ensure all fields are valid and min amount ≤ max amount.")

# Show Rules
if st.session_state.rules:
    st.subheader("📋 Defined Rules")
    for i, rule in enumerate(st.session_state.rules):
        logic_text = f"{rule['logic']}"
        st.markdown(f"**{i+1}.** If Supplier = '{rule['supplier']}' {logic_text} Amount between {rule['min_amount']} - {rule['max_amount']} → **{rule['category']}**")
        if st.button("❌ Delete", key=f"del_{i}"):
            st.session_state.rules.pop(i)
            st.rerun()

    # Save Rules to JSON
    if st.button("💾 Save Rules to JSON"):
        try:
            with open("rules.json", "w") as f:
                json.dump(st.session_state.rules, f, indent=2)
            st.success("✅ Rules saved to rules.json")
        except Exception as e:
            st.error(f"❌ Failed to save: {e}")

# Apply Rules
if uploaded_file is not None and not df.empty and st.session_state.rules:
    st.subheader("🚀 Apply Rules")

    def match_rule(row, rule):
        try:
            supplier_match = str(row.get("Supplier", "")).strip().lower() == rule["supplier"]
            amount = float(row.get("Amount", 0))
            amount_match = rule["min_amount"] <= amount <= rule["max_amount"]

            if rule["logic"] == "AND" and supplier_match and amount_match:
                return rule["category"], "Supplier AND Amount"
            elif rule["logic"] == "OR" and (supplier_match or amount_match):
                return rule["category"], "Supplier OR Amount"
            else:
                return "Uncategorized", "None"
        except Exception as e:
            return "Uncategorized", f"Error: {str(e)}"

    for idx, rule in enumerate(st.session_state.rules):
        try:
            rule_df = df.copy()
            rule_df["Category"], rule_df["Rule_Applied"] = zip(*rule_df.apply(lambda row: match_rule(row, rule), axis=1))
            rule_df = rule_df[rule_df["Category"] == rule["category"]].copy()

            st.markdown(f"### 🎯 Rule {idx+1} Output — Category: {rule['category']}")
            st.dataframe(rule_df, use_container_width=True)

            csv_rule = rule_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"⬇️ Download Output for Rule {idx+1}",
                data=csv_rule,
                file_name=f"rule_{idx+1}_output.csv",
                mime="text/csv",
                key=f"download_{idx}"
            )
        except Exception as e:
            st.error(f"❌ Error applying Rule {idx+1}: {e}")
