import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re
from PIL import Image
from streamlit_cropper import st_cropper


# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="🧠 CA Firm AI Dashboard & Automated Financial Processing", layout="wide")

# ------------------ SESSION INITIALIZATION ------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = True  # Simulate post-login for now
if "current_page" not in st.session_state:
    st.session_state.current_page = "home" # Initial page is "home"
if "upload_history" not in st.session_state:
    st.session_state.upload_history = []
if "upload_errors" not in st.session_state:
    st.session_state.upload_errors = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "Username": "vivek_birla",
        "Full Name": "Vivek Birla",
        "Email": "vivek@example.com",
        "Phone": "9876543210",
        "Avatar": "https://www.w3schools.com/howto/img_avatar.png"
    }
if "show_account_menu" not in st.session_state:
    st.session_state.show_account_menu = False


# ------------------ HELPER FUNCTIONS (CSS and Navigation) ------------------
def render_header():
    # Modern CSS with better color scheme and typography
    st.markdown("""
        <style>
        /* Global App Styling */
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* Main content area */
        .main .block-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            margin-top: 1rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        /* Header styling */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0px;
            position: relative;
            z-index: 1000;
            border-bottom: 2px solid #e0e6ed;
            margin-bottom: 20px;
        }
        
        /* Title styling */
        .main h2 {
            color: #2c3e50;
            font-weight: 700;
            font-size: 2.2rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 0;
        }
        
        /* Fix text colors throughout the app */
        .main p, .main div, .main span, .main label {
            color: #2c3e50 !important;
        }
        
        /* Form labels */
        .stTextInput > label, .stSelectbox > label, .stFileUploader > label {
            color: #2c3e50 !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }
        
        /* Hide unwanted labels */
        .stFileUploader > label[data-testid="stWidgetLabel"] {
            display: none !important;
        }
        
        /* Avatar button styling */
        .stButton > button[data-testid="baseButton-header"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 1.5rem;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        
        .stButton > button[data-testid="baseButton-header"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        /* Floating menu with glassmorphism */
        .floating-menu {
            position: fixed;
            top: 90px;
            right: 30px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            z-index: 9999;
            width: 220px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }
        
        .floating-menu .stButton button {
            width: 100%;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 12px;
            padding: 12px 16px;
            border: none;
            color: white;
            font-size: 14px;
            font-weight: 600;
            text-align: left;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
        }
        
        .floating-menu .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(240, 147, 251, 0.5);
        }
        
        /* Back button styling */
        .back-button {
            position: fixed;
            top: 30px;
            left: 30px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 10px 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        /* Primary buttons (Get Started, etc.) */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1.3rem;
            font-weight: 700;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }
        
        /* Secondary buttons */
        .stButton > button:not([kind="primary"]) {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #2c3e50;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(132, 250, 176, 0.3);
        }
        
        .stButton > button:not([kind="primary"]):hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(132, 250, 176, 0.5);
        }
        
        /* Cards for services */
        .service-card {
            background: linear-gradient(135deg, #fff 0%, #f8f9ff 100%);
            border-radius: 20px;
            padding: 30px;
            margin: 15px 0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
        }
        
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }
        
        .service-card h3 {
            color: #2c3e50 !important;
            font-weight: 700;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .service-card p {
            color: #5a6c7d !important;
            line-height: 1.6;
            font-size: 1rem;
        }
        
        /* Form styling */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #e0e6ed;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 1rem;
            transition: all 0.3s ease;
            color: #2c3e50 !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* File uploader styling */
        .stFileUploader > div {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 15px;
            padding: 30px;
            border: 2px dashed rgba(255, 255, 255, 0.3);
            text-align: center;
        }
        
        .stFileUploader div[data-testid="stFileUploaderDropzone"] {
            color: white !important;
        }
        
        .stFileUploader div[data-testid="stFileUploaderDropzone"] span {
            color: white !important;
        }
        
        /* Dataframe styling */
        .stDataFrame {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        }
        
        /* Success/Error messages */
        .stSuccess {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            border-radius: 12px;
            border: none;
        }
        
        .stError {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-radius: 12px;
            border: none;
        }
        
        .stWarning {
            background: linear-gradient(135deg, #fff9c4 0%, #f4e2d8 100%);
            border-radius: 12px;
            border: none;
        }
        
        .stInfo {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-radius: 12px;
            border: none;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            font-weight: 600;
        }
        
        /* Center text utility */
        .center-text {
            text-align: center;
            color: #2c3e50 !important;
            font-weight: 600;
        }
        
        /* Welcome section */
        .welcome-section {
            text-align: center;
            padding: 40px 0;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border-radius: 20px;
            margin-bottom: 30px;
        }
        
        .welcome-section h1 {
            color: #2c3e50 !important;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 20px;
            text-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .welcome-section p {
            color: #5a6c7d !important;
            font-size: 1.2rem;
            margin-bottom: 30px;
        }
        
        /* Get Started button container */
        .get-started-container {
            text-align: center;
            padding: 30px 0;
            margin-top: 20px;
        }
        
        /* Section dividers */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 30px 0;
            border-radius: 2px;
        }
        
        /* Profile image styling */
        .profile-image {
            border-radius: 50%;
            border: 4px solid #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        </style>
    """, unsafe_allow_html=True)

    header_col1, header_col2 = st.columns([1, 0.1])

    with header_col1:
        st.markdown("## 🧠 CA Firm AI Dashboard & Automated Financial Processing")

    with header_col2:
        # Avatar button
        if st.button("👤", key="avatar_button", help="Account Menu"):
            st.session_state.show_account_menu = not st.session_state.show_account_menu
            st.rerun()

    # Floating account menu
    if st.session_state.show_account_menu:
        with st.container():
            st.markdown('<div class="floating-menu">', unsafe_allow_html=True)
            
            if st.button("🏠 Home", key="home_btn_menu", use_container_width=True):
                st.session_state.current_page = "home"
                st.session_state.show_account_menu = False
                st.rerun()

            if st.button("👤 My Profile", key="profile_btn_menu", use_container_width=True):
                st.session_state.current_page = "profile"
                st.session_state.show_account_menu = False
                st.rerun()
            
            if st.button("🔒 Change Password", key="password_btn_menu", use_container_width=True):
                st.session_state.current_page = "change_password"
                st.session_state.show_account_menu = False
                st.rerun()
            
            if st.button("🚪 Sign Out", key="signout_btn_menu", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_page = "login"
                st.session_state.show_account_menu = False
                st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------ LOGIN PAGE ------------------
def show_login_page():
    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>🔐 Welcome Back</h1>', unsafe_allow_html=True)
    st.markdown('<p>Please sign in to access your CA Dashboard</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_btn = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if login_btn:
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.current_page = "home"
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Please enter both username and password")

# ------------------ PROFILE PAGE ------------------
def show_profile_page():
    # Back button
    if st.button("⬅️ Back to Home", key="back_to_home_profile", help="Return to home page"):
        st.session_state.current_page = "home"
        st.session_state.show_account_menu = False
        st.rerun()
    
    render_header()
    
    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>👤 My Profile</h1>', unsafe_allow_html=True)
    st.markdown('<p>Manage your account information and settings</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    user_data = st.session_state.user_profile

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Profile Picture")
        if user_data.get("Avatar"):
            try:
                if os.path.exists(user_data["Avatar"]):
                    st.image(user_data["Avatar"], width=200, caption="Current Profile Picture")
                else:
                    st.image(user_data["Avatar"], width=200, caption="Current Profile Picture")
            except:
                st.info("No profile picture available")
    
    with col2:
        with st.form(key="profile_form"):
            st.markdown("### 📄 Your Details")

            full_name = st.text_input("Full Name", value=user_data.get("Full Name", ""))
            email = st.text_input("Email", value=user_data.get("Email", ""))
            phone = st.text_input("Phone Number", value=user_data.get("Phone", ""))

            st.markdown("#### Upload & Crop Profile Picture")
            avatar_file = st.file_uploader("Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"], key="avatar_upload")

            cropped_image = None
            if avatar_file:
                try:
                    image = Image.open(avatar_file)
                    st.markdown("##### Crop Your Image:")
                    cropped_image = st_cropper(image, aspect_ratio=(1, 1), box_color='#667eea')

                    st.markdown("##### Cropped Image Preview:")
                    st.image(cropped_image, width=150)
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")

            submit = st.form_submit_button("Update Profile", type="primary", use_container_width=True)

            if submit:
                st.session_state.user_profile["Full Name"] = full_name
                st.session_state.user_profile["Email"] = email
                st.session_state.user_profile["Phone"] = phone

                if cropped_image:
                    try:
                        resized_image = cropped_image.resize((150, 150))
                        avatar_path = f"uploaded_avatar_{user_data.get('Username', 'user')}.png"
                        resized_image.save(avatar_path)
                        st.session_state.user_profile["Avatar"] = avatar_path
                        st.success("✅ Profile picture updated successfully!")
                    except Exception as e:
                        st.error(f"Error saving profile picture: {str(e)}")

                st.success("✅ Profile updated successfully!")
                st.rerun()

# ------------------ PASSWORD RULE CHECK ------------------
def is_strong_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*]", password):
        return "Password must contain at least one special character (!@#$%^&*)."
    return "Valid"

# ------------------ CHANGE PASSWORD PAGE ------------------
def show_change_password_page():
    # Back button
    if st.button("⬅️ Back to Home", key="back_to_home_password", help="Return to home page"):
        st.session_state.current_page = "home"
        st.session_state.show_account_menu = False
        st.rerun()
    
    render_header()
    
    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>🔒 Change Password</h1>', unsafe_allow_html=True)
    st.markdown('<p>Update your account password securely</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("#### Password Requirements:")
        st.markdown("✓ Minimum 8 characters")
        st.markdown("✓ At least 1 uppercase letter")  
        st.markdown("✓ At least 1 lowercase letter")
        st.markdown("✓ At least 1 number")
        st.markdown("✓ At least 1 special character (`!@#$%^&*`)")
        st.markdown('</div>', unsafe_allow_html=True)

        with st.form(key="change_password_form", clear_on_submit=True):
            current_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")

            submit_button = st.form_submit_button(label="Change Password", type="primary", use_container_width=True)

            if submit_button:
                if not current_password or not new_password or not confirm_password:
                    st.warning("⚠️ Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("❌ New Password and Confirm Password do not match.")
                else:
                    password_check = is_strong_password(new_password)
                    if password_check == "Valid":
                        st.success("✅ Password changed successfully!")
                    else:
                        st.error(f"❌ {password_check}")

# ------------------ SERVICES SECTION ------------------
def render_services_section():
    st.markdown("---")
    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>🚀 Our AI-Powered Services</h1>', unsafe_allow_html=True)
    st.markdown('<p>Advanced financial processing solutions for modern CA firms</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Duplicate Detection")
        st.markdown("Identify duplicate transactions across large datasets to ensure data accuracy and prevent redundancy.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("### 📂 Transaction Categorization")
        st.markdown("Automatically classify transactions into appropriate categories to simplify financial reporting.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("### 📊 OCR Extraction")
        st.markdown("Extract valuable data from scanned receipts and documents using Optical Character Recognition (OCR).")
        st.markdown('</div>', unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    with col4:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("### 🕵️ Fraud Detection")
        st.markdown("Detect fraudulent transactions using advanced anomaly detection techniques to secure your financial data.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="service-card">', unsafe_allow_html=True)
        st.markdown("### 🔗 Transaction Matching")
        st.markdown("Efficiently match transactions across different accounts and ledgers to ensure consistency and accuracy.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Move Get Started button here - after services description
    st.markdown('<div class="get-started-container">', unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        if st.button("🚀 Get Started", key="get_started_button", type="primary", help="Start uploading your files for processing"):
            st.session_state.current_page = "upload_section"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

# ------------------ FILE UPLOAD SECTION ------------------
def show_upload_section():
    # Back button
    if st.button("⬅️ Back to Home", key="back_to_home_upload", help="Return to home page"):
        st.session_state.current_page = "home"
        st.rerun()

    render_header()
    
    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>📂 File Upload Center</h1>', unsafe_allow_html=True)
    st.markdown('<p>Upload your financial documents for AI-powered processing</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Supported formats: `.csv`, `.txt`, `.pdf`, `.png`, `.jpg`, `.jpeg`")

    # Clear previous errors
    st.session_state.upload_errors = []

    uploaded_files = st.file_uploader(
        "",
        type=["csv", "txt", "pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Upload your files here"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            file_ext = os.path.splitext(filename)[-1].lower()
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validation_status = "✅ Passed"

            try:
                supported_extensions = [".csv", ".txt", ".pdf", ".png", ".jpg", ".jpeg"]
                if file_ext not in supported_extensions:
                    raise ValueError(f"Unsupported file format: {file_ext}")

                st.markdown('<div class="service-card">', unsafe_allow_html=True)
                st.markdown(f"### 📄 File: `{filename}`")

                if file_ext == ".csv":
                    df = pd.read_csv(uploaded_file)
                    st.success("CSV file uploaded successfully!")
                    st.dataframe(df.head(15), use_container_width=True)

                elif file_ext == ".txt":
                    uploaded_file.seek(0)
                    text = uploaded_file.read().decode("utf-8")
                    lines = text.strip().splitlines()[:15]
                    st.success("Text file uploaded successfully!")
                    st.code("\n".join(lines))

                elif file_ext in [".png", ".jpg", ".jpeg"]:
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    st.success("Image uploaded successfully!")
                    st.image(image, caption=filename, use_container_width=True)

                elif file_ext == ".pdf":
                    st.success("PDF uploaded successfully! Preview not supported.")

                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                validation_status = "❌ Failed"
                error_msg = f"❌ {filename}: {str(e)}"
                st.session_state.upload_errors.append(error_msg)
                st.error(error_msg)

            st.session_state.upload_history.append({
                "Date": date_now,
                "Filename": filename,
                "Extension": file_ext,
                "Validation Check": validation_status
            })

    # Show upload history
    if st.session_state.upload_history:
        st.markdown("---")
        with st.expander("📜 Upload History (Click to Expand)", expanded=True):
            hist_df = pd.DataFrame(st.session_state.upload_history)
            # Show most recent uploads first
            hist_df = hist_df.iloc[::-1].reset_index(drop=True)
            st.dataframe(hist_df, use_container_width=True)

# ------------------ HOME PAGE ------------------
def show_home_page():
    render_header()

    st.markdown('<div class="welcome-section">', unsafe_allow_html=True)
    st.markdown('<h1>Welcome to CA Firm AI Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p>Streamline your financial processes with cutting-edge AI technology</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    render_services_section()

# ------------------ MAIN APP LOGIC ------------------
def main():
    # Handle authentication
    if not st.session_state.get("authenticated", False):
        show_login_page()
        return

    # Handle page routing using session state
    current_page = st.session_state.get("current_page", "home")
    
    if current_page == "home":
        show_home_page()
    elif current_page == "upload_section":
        show_upload_section()
    elif current_page == "profile":
        show_profile_page()
    elif current_page == "change_password":
        show_change_password_page()
    else:
        # Fallback to home if state is somehow invalid
        st.session_state.current_page = "home"
        st.rerun()

if __name__ == "__main__":
    main()