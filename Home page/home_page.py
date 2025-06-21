import streamlit as st
import pandas as pd
from datetime import datetime
import os
from PIL import Image

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Secure Dashboard", layout="wide")

# ------------------ SESSION INITIALIZATION ------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True  # simulate post-login for now
if "current_page" not in st.session_state:
    st.session_state.current_page = "upload"
if "upload_history" not in st.session_state:
    st.session_state.upload_history = []
if "upload_errors" not in st.session_state:
    st.session_state.upload_errors = []


# ------------------ PAGES ------------------

def show_profile_page():
    st.title("👤 My Profile")
    if st.button("⬅️ Back to Main Page"):
        st.session_state.current_page = "upload"
        st.rerun()
    st.markdown("This is a placeholder profile page.")
    st.info("Add user details, avatar, etc. later.")


def show_change_password_page():
    st.title("🔒 Change Password")
    if st.button("⬅️ Back to Main Page"):
        st.session_state.current_page = "upload"
        st.rerun()
    st.markdown("This is a placeholder password change page.")
    st.info("Add secure password update form here.")



def show_login_page():
    st.title("🔐 Please Log In")
    st.warning("This is the login page (not implemented here).")


def show_upload_page():
    # ---------- PROFILE MENU ----------
    top_col1, top_col2 = st.columns([9, 1])
    with top_col2:
        with st.popover("👤"):
            st.markdown("### Account Options")
            if st.button("My Profile"):
                st.session_state.current_page = "profile"
                st.rerun()
            if st.button("Change Password"):
                st.session_state.current_page = "change_password"
                st.rerun()
            if st.button("Sign Out"):
                st.session_state.authenticated = False
                st.session_state.current_page = "login"
                st.rerun()

    # ---------- PAGE CONTENT ----------
    st.title("📁 File Upload Dashboard")
    st.markdown("Supported formats: `.csv`, `.txt`, `.pdf`, `.png`, `.jpg`, `.jpeg`")

    allowed_types = {
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }

    uploaded_files = st.file_uploader(
        "Upload your files",
        type=None,
        accept_multiple_files=True
    )

    # Clear previous errors
    st.session_state.upload_errors.clear()

    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            file_ext = os.path.splitext(filename)[-1].lower()
            file_type = uploaded_file.type
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validation_status = "✅ Passed"

            try:
                if file_ext not in allowed_types:
                    raise ValueError("Unsupported file extension.")

                if file_type != allowed_types[file_ext]:
                    raise ValueError(f"MIME mismatch: expected {allowed_types[file_ext]}, got {file_type}")

                st.markdown(f"---\n### 📄 File: `{filename}`")

                if file_ext == ".csv":
                    df = pd.read_csv(uploaded_file)
                    st.success("CSV file preview:")
                    st.dataframe(df.head(15), use_container_width=True)

                elif file_ext == ".txt":
                    text = uploaded_file.read().decode("utf-8")
                    lines = text.strip().splitlines()[:15]
                    st.success("Text file preview:")
                    st.text("\n".join(lines))

                elif file_ext in [".png", ".jpg", ".jpeg"]:
                    image = Image.open(uploaded_file)
                    image.verify()
                    st.image(uploaded_file, caption=filename, use_container_width=True)

                elif file_ext == ".pdf":
                    st.info("PDF uploaded. Preview not supported.")

            except Exception as e:
                validation_status = "❌ Failed"
                st.session_state.upload_errors.append(f"❌ {filename}: {str(e)}")

            # Append to upload history
            st.session_state.upload_history.append({
                "Date": date_now,
                "Filename": filename,
                "Extension": file_ext,
                "Validation Check": validation_status
            })

    # Show errors
    if st.session_state.upload_errors:
        st.error("⚠️ Some files failed to upload.")
        for err in st.session_state.upload_errors:
            st.warning(err)

    # Upload history
    if st.session_state.upload_history:
        st.markdown("---")
        st.markdown("### 📜 Upload History")
        hist_df = pd.DataFrame(st.session_state.upload_history)
        st.dataframe(hist_df, use_container_width=True)


# ------------------ PAGE ROUTING ------------------

if not st.session_state.get("authenticated", False):
    show_login_page()
else:
    current = st.session_state.get("current_page", "upload")
    if current == "upload":
        show_upload_page()
    elif current == "profile":
        show_profile_page()
    elif current == "change_password":
        show_change_password_page()
