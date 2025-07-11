import streamlit as st
import requests
import pandas as pd
import json
import tempfile
from PIL import Image
import os

st.set_page_config(page_title="🧾 Receipt & Invoice Parser", page_icon="🧾", layout="wide")

st.title("🧾 Smart Receipt/Invoice/Bank Statement Parser")

# Tabs setup
tab1, tab2, tab3 = st.tabs([
    "📑 Invoice & Receipt PDFs",
    "🖼️ Invoice & Receipt Images",
    "🏦 Bank Statement"
])

# Tab 1: Invoice and Receipt PDFs
with tab1:
    st.header("Upload Invoice or Receipt PDF")

    doc_type = st.radio("Select document type:", ["Invoice", "Receipt"], horizontal=True, key="pdf_doc_type")
    pdf_file = st.file_uploader(
        f"Upload a {doc_type.lower()} file (PDF)",
        type=["pdf"],
        key=f"{doc_type.lower()}_pdf"
    )

    if pdf_file and st.button(f"🚀 Extract {doc_type}", key=f"extract_{doc_type.lower()}_btn"):
        with st.spinner(f"🔍 Analyzing {doc_type.lower()}..."):
            try:
                endpoint = "http://localhost:8000/parse-invoice/" if doc_type == "Invoice" else "http://localhost:8000/parse-receipt/"
                response = requests.post(
                    endpoint,
                    files={"file": (pdf_file.name, pdf_file.getvalue(), pdf_file.type)},
                    timeout=600
                )

                if response.status_code == 200:
                    data = response.json()

                    if "error" in data:
                        st.warning(f"⚠️ {data['error']}")
                    else:
                        # Summary Table
                        st.markdown(f"### 📌 {doc_type} Summary")
                        if doc_type == "Invoice":
                            summary = {
                                "Supplier Name": data.get("supplier_name", ""),
                                "Invoice Date": data.get("invoice_date", ""),
                                "Due Date": data.get("due_date", ""),
                                "Currency": data.get("currency", ""),
                                "Total Amount": data.get("total_amount", ""),
                                "Tax Amount": data.get("tax_amount", "")
                            }
                        else:
                            summary = {
                                "Store Name": data.get("store_name", ""),
                                "Date": data.get("date", ""),
                                "Currency": data.get("currency", ""),
                                "Total Amount": data.get("total_amount", ""),
                                "Tax Details": data.get("tax_details", ""),
                                "Transaction Number": data.get("transaction_number", ""),
                                "Card Details": data.get("card_details", ""),
                                "Service Fee": data.get("service_fee", "")
                            }

                        st.table(pd.DataFrame(summary.items(), columns=["Field", "Value"]))

                        # Items Table
                        st.markdown(f"### 🛒 {doc_type} Items")
                        items = data.get("items", [])
                        if items:
                            st.dataframe(pd.DataFrame(items).replace("", "—"), use_container_width=True)
                        else:
                            st.info(f"No items found in the {doc_type.lower()}.")

                        # JSON Download
                        st.download_button(
                            label="💾 Download JSON",
                            data=json.dumps(data, indent=2),
                            file_name=f"{doc_type.lower()}_data.json",
                            mime="application/json"
                        )
                else:
                    st.error(f"❌ Server returned {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"⚠️ Exception occurred: {e}")

# Tab 2: Invoice and Receipt Images
with tab2:
    st.header("Upload Invoice or Receipt Image")

    doc_type = st.radio("Choose the document type to process:", ["Invoice", "Receipt"], horizontal=True, key="image_doc_type")
    uploaded_file = st.file_uploader(
        f"Upload a {doc_type.lower()} image",
        type=["png", "jpg", "jpeg"],
        key=f"{doc_type.lower()}_image"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 2])
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with col1:
            img = Image.open(tmp_path)
            rotated_img = img.rotate(-90, expand=True)
            st.image(rotated_img, caption=f"Uploaded {doc_type} (Rotated -90°)", use_container_width=True)

        with col2:
            st.markdown(f"#### 🧠 Extracted {doc_type} Information")
            result_tab1, result_tab2 = st.tabs(["Parsed Output", "Raw Output"])
            with st.spinner(f"Analyzing {doc_type.lower()} .."):
                try:
                    with open(tmp_path, "rb") as f:
                        files = {"file": (uploaded_file.name, f, uploaded_file.type)}
                        endpoint = "http://localhost:8000/api/invoice" if doc_type == "Invoice" else "http://localhost:8000/api/receipt"
                        response = requests.post(endpoint, files=files)
                    response.raise_for_status()
                    json_data = response.json()
                except requests.exceptions.HTTPError as http_err:
                    with result_tab1:
                        st.error(f"HTTP error processing {doc_type.lower()}: {str(http_err)}")
                        if doc_type == "Invoice":
                            st.table(pd.DataFrame.from_dict({
                                "Supplier Name": [""],
                                "Invoice Date": [""],
                                "Total Amount": [""],
                                "Tax Amount": [""],
                                "Due Date": [""],
                                "Currency": [""],
                            }, orient="index", columns=["Value"]))
                            st.table(pd.DataFrame(columns=["description", "quantity", "unit_price", "total_price"]))
                        else:
                            st.table(pd.DataFrame.from_dict({
                                "Store Name": [""],
                                "Date": [""],
                                "Currency": [""],
                                "Total Amount": [""],
                                "Tax Details": [""],
                                "Transaction Number": [""],
                                "Card Details": [""],
                                "Service Fee": [""],
                            }, orient="index", columns=["Value"]))
                            st.table(pd.DataFrame(columns=["name", "description", "price", "unit_price", "quantity", "discount", "total", "line_total"]))
                    with result_tab2:
                        st.error(f"Raw output error: {str(http_err)}")
                        st.code(str(http_err))
                    st.stop()
                except Exception as e:
                    with result_tab1:
                        st.error(f"Error processing {doc_type.lower()}: {str(e)}")
                        if doc_type == "Invoice":
                            st.table(pd.DataFrame.from_dict({
                                "Supplier Name": [""],
                                "Invoice Date": [""],
                                "Total Amount": [""],
                                "Tax Amount": [""],
                                "Due Date": [""],
                                "Currency": [""],
                            }, orient="index", columns=["Value"]))
                            st.table(pd.DataFrame(columns=["description", "quantity", "unit_price", "total_price"]))
                        else:
                            st.table(pd.DataFrame.from_dict({
                                "Store Name": [""],
                                "Date": [""],
                                "Currency": [""],
                                "Total Amount": [""],
                                "Tax Details": [""],
                                "Transaction Number": [""],
                                "Card Details": [""],
                                "Service Fee": [""],
                            }, orient="index", columns=["Value"]))
                            st.table(pd.DataFrame(columns=["name", "description", "price", "unit_price", "quantity", "discount", "total", "line_total"]))
                    with result_tab2:
                        st.error(f"Raw output error: {str(e)}")
                        st.code(str(e))
                    st.stop()
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                with result_tab1:
                    st.subheader("🔹 Summary Fields")
                    if doc_type == "Invoice":
                        summary_fields = {
                            "Supplier Name": json_data.get("supplier_name", ""),
                            "Invoice Date": json_data.get("invoice_date", ""),
                            "Total Amount": json_data.get("total_amount", ""),
                            "Tax Amount": json_data.get("tax_amount", ""),
                            "Due Date": json_data.get("due_date", ""),
                            "Currency": json_data.get("currency", "")
                        }
                        item_fields = ["description", "quantity", "unit_price", "total_price"]
                    else:
                        summary_fields = {
                            "Store Name": json_data.get("store_name", ""),
                            "Date": json_data.get("date", ""),
                            "Currency": json_data.get("currency", ""),
                            "Total Amount": json_data.get("total_amount", ""),
                            "Tax Details": json_data.get("tax_details", ""),
                            "Transaction Number": json_data.get("transaction_number", ""),
                            "Card Details": json_data.get("card_details", ""),
                            "Service Fee": json_data.get("service_fee", "")
                        }
                        item_fields = ["name", "description", "price", "unit_price", "quantity", "discount", "total", "line_total"]

                    st.table(pd.DataFrame.from_dict(summary_fields, orient="index", columns=["Value"]))
                    st.subheader(f"🛒 {doc_type} Items")
                    items = json_data.get("items", [])
                    if items and isinstance(items, list) and len(items) > 0:
                        df_items = pd.DataFrame(items)
                        for col in item_fields:
                            if col not in df_items.columns:
                                df_items[col] = ""
                        df_items = df_items[item_fields]
                        st.table(df_items)
                    else:
                        st.info(f"No items found in {doc_type.lower()}.")
                        st.table(pd.DataFrame(columns=item_fields))

                with result_tab2:
                    st.subheader("📝 Raw JSON Output")
                    st.code(json.dumps(json_data, indent=2))

    else:
        st.info(f"Please upload a {doc_type.lower()} image to proceed.")

# Tab 3: Bank Statement
with tab3:
    st.header("Bank Statement Extractor")

    uploaded_file = st.file_uploader("📤 Upload Bank Statement PDF", type=["pdf"], key="bank_pdf_upload")

    if uploaded_file:
        st.info("📨 Uploading to server and extracting...")

        try:
            response = requests.post(
                "http://localhost:8000/parse-bank-statement/",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                timeout=600
            )

            if response.status_code != 200:
                st.error(f"❌ API Error {response.status_code}: {response.json().get('error', 'Unknown')}")
            else:
                result = response.json().get("result", {})
                
                # Top Summary
                st.subheader("📌 Account Summary")
                summary_fields = {
                    "Account Holder": result.get("account_holder_name", "–"),
                    "Account Number": result.get("account_number", "–"),
                    "Bank Name": result.get("bank_name", "–"),
                    "Statement Period": result.get("statement_period", "–"),
                    "Currency": result.get("currency", "–"),
                    "Opening Balance": result.get("opening_balance", "–"),
                    "Closing Balance": result.get("closing_balance", "–"),
                }

                st.table(pd.DataFrame(summary_fields.items(), columns=["Field", "Value"]))

                # Transactions Table
                st.subheader("📋 Transactions")
                transactions = result.get("transactions", [])
                if transactions:
                    df = pd.DataFrame(transactions)
                    df["money_in"] = df["money_in"].fillna("–")
                    df["money_out"] = df["money_out"].fillna("–")
                    df["balance"] = df["balance"].fillna("–")
                    st.dataframe(
                        df[["date", "description", "money_in", "money_out", "balance"]],
                        use_container_width=True
                    )
                    st.download_button(
                        label="💾 Download Full JSON",
                        data=json.dumps(result, indent=2),
                        file_name="parsed_bank_statement.json",
                        mime="application/json"
                    )
                else:
                    st.warning("⚠️ No transactions found.")
        except Exception as e:
            st.error(f"⚠️ Failed to process file: {str(e)}")