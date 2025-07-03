# create multi rule based system 
import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Advanced Rule Engine", layout="wide")
st.title("🧠 Priority-Based Rule Engine")

if "rules" not in st.session_state:
    st.session_state.rules = []

st.subheader("📁 Upload CSV")
uploaded_file = st.file_uploader("Upload your data file", type=["csv"])
df = pd.DataFrame()
supplier_options, description_keywords, date_columns = [], [], []

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded!")
    st.dataframe(df, use_container_width=True)
    if "Supplier" in df.columns:
        supplier_options = sorted(df["Supplier"].dropna().astype(str).unique())
    if "Description" in df.columns:
        description_keywords = sorted(df["Description"].dropna().astype(str).unique())
    date_columns = [col for col in df.columns if "date" in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col])]

st.subheader("➕ Create Rule with Two Conditions")
field_options = ["--Select--", "Supplier", "Amount", "Description"] + date_columns

field1 = st.selectbox("Select First Field", field_options, key="field1")
input1 = {}
if field1 == "Supplier" and supplier_options:
    input1["value"] = st.selectbox("Select Supplier", ["--Select--"] + supplier_options, key="val1")
elif field1 == "Amount":
    col1, col2 = st.columns(2)
    input1["min"] = col1.number_input("Minimum Amount", key="min1")
    input1["max"] = col2.number_input("Maximum Amount", key="max1")
elif field1 == "Description":
    input1["value"] = st.text_input("Keyword in Description", key="desc1")
elif field1 in date_columns:
    col1, col2 = st.columns(2)
    input1["start"] = col1.date_input("Start Date", key="start1")
    input1["end"] = col2.date_input("End Date", key="end1")

logic = st.radio("Logic Between Conditions", ["AND", "OR"], horizontal=True)

field2 = st.selectbox("Select Second Field", field_options, key="field2")
input2 = {}
if field2 == "Supplier" and supplier_options:
    input2["value"] = st.selectbox("Select Supplier", ["--Select--"] + supplier_options, key="val2")
elif field2 == "Amount":
    col1, col2 = st.columns(2)
    input2["min"] = col1.number_input("Minimum Amount", key="min2")
    input2["max"] = col2.number_input("Maximum Amount", key="max2")
elif field2 == "Description":
    input2["value"] = st.text_input("Keyword in Description", key="desc2")
elif field2 in date_columns:
    col1, col2 = st.columns(2)
    input2["start"] = col1.date_input("Start Date", key="start2")
    input2["end"] = col2.date_input("End Date", key="end2")

category_list = [
    "--Select--", "Stationery", "Consulting", "Training", "Maintenance", "Insurance",
    "Miscellaneous", "Travel", "Office Supplies", "Utilities", "Marketing", "IT Services"
]
category = st.selectbox("Select Category", category_list)

if st.button("✅ Add Rule"):
    if field1 != "--Select--" and field2 != "--Select--" and category != "--Select--":
        rule = {
            "field1": field1, "input1": input1,
            "field2": field2, "input2": input2,
            "logic": logic, "category": category
        }
        st.session_state.rules.append(rule)
        st.success("✅ Rule added!")
    else:
        st.warning("⚠️ Please complete all fields.")

if st.session_state.rules:
    st.subheader("📋 Defined Rules")
    for i, r in enumerate(st.session_state.rules):
        st.markdown(f"**{i+1}.** If {r['field1']} + {r['field2']} → {r['logic']} → **{r['category']}**")
        if st.button("❌ Delete", key=f"del_{i}"):
            st.session_state.rules.pop(i)
            st.rerun()
    if st.button("💾 Save Rules to JSON"):
        with open("rules.json", "w") as f:
            json.dump(st.session_state.rules, f, indent=2)
        st.success("✅ Rules saved to rules.json")

if uploaded_file and not df.empty and st.session_state.rules:
    st.subheader("🚀 Apply Rules")

    def match(row, rule):
        def check_condition(field, inputs):
            if field == "Supplier":
                return str(row.get("Supplier", "")).strip().lower() == inputs.get("value", "").lower()
            elif field == "Amount":
                try:
                    val = float(row.get("Amount", 0))
                    return inputs["min"] <= val <= inputs["max"]
                except:
                    return False
            elif field == "Description":
                return inputs.get("value", "").lower() in str(row.get("Description", "")).strip().lower()
            elif field in df.columns:
                try:
                    dt = pd.to_datetime(row.get(field)).date()
                    return inputs["start"] <= dt <= inputs["end"]
                except:
                    return False
            return False

        cond1 = check_condition(rule["field1"], rule["input1"])
        cond2 = check_condition(rule["field2"], rule["input2"])
        if rule["logic"] == "AND" and cond1 and cond2:
            return rule["category"], f"{rule['field1']} AND {rule['field2']}"
        elif rule["logic"] == "OR" and (cond1 or cond2):
            return rule["category"], f"{rule['field1']} OR {rule['field2']}"
        return "Uncategorized", "None"

    df["Category"], df["Rule_Applied"] = zip(*df.apply(lambda row: match(row, st.session_state.rules[-1]), axis=1))
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ Download Categorized CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="categorized_output.csv")
