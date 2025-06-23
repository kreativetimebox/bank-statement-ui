import streamlit as st
import sqlite3
import hashlib

# Set up page
st.set_page_config(page_title="Streamlit Auth App", layout="wide")

# Inject CSS for background and dark theme + white buttons
st.markdown("""
    <style>
        body {
            background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: white;
        }
        .stApp {
            background-color: rgba(0, 0, 0, 0.7);
            padding: 2rem;
            border-radius: 15px;
        }
        input, textarea {
            color: black !important;
        }
        button[kind="primary"] {
            background-color: white !important;
            color: black !important;
            font-weight: bold;
            border-radius: 8px;
            padding: 8px 16px;
        }
        .css-1cpxqw2, .css-1kyxreq, .css-ffhzg2 {
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Database Setup ----------
def create_connection():
    return sqlite3.connect("users.db")

def create_users_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT UNIQUE,
                        company TEXT,
                        mobile TEXT CHECK(length(mobile) = 10),
                        password TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(name, email, company, mobile, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, company, mobile, password) VALUES (?, ?, ?, ?, ?)",
                       (name, email, company, mobile, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?",
                   (email, hash_password(password)))
    result = cursor.fetchone()
    conn.close()
    return result

def update_password(email, new_password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(new_password), email))
    conn.commit()
    conn.close()

# ---------- App Navigation ----------
PAGES = ["Home", "Account", "About"]
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

with st.sidebar:
    st.title("Navigation")
    selected_page = st.radio("Go to", PAGES)
    st.session_state.nav_page = selected_page

# ---------- Home Page ----------
if st.session_state.nav_page == "Home":
    st.title("Welcome To Kreative TimeBox")
    st.write("This is the landing/home page for your platform. Use the sidebar to navigate.")

# ---------- Account Page ----------
elif st.session_state.nav_page == "Account":
    create_users_table()
    if "account_page" not in st.session_state:
        st.session_state.account_page = "choice"

    def reset_account_page():
        st.session_state.account_page = "choice"

    if st.session_state.account_page == "choice":
        st.title("Account")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login"):
                st.session_state.account_page = "login"
                st.rerun()
        with col2:
            if st.button("Register"):
                st.session_state.account_page = "register"
                st.rerun()

    elif st.session_state.account_page == "login":
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="login_submit"):
            user = authenticate_user(email, password)
            if user:
                st.success("Login successful!")
                st.session_state.account_page = "logged_in"
                st.rerun()
            else:
                st.error("Invalid credentials")

        if st.button("Forgot Password?"):
            st.session_state.account_page = "forgot_password"
            st.rerun()

        if st.button("Go Back", key="back_login"):
            reset_account_page()
            st.rerun()

    elif st.session_state.account_page == "register":
        st.subheader("Register")
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        company = st.text_input("Company", key="reg_company")
        mobile = st.text_input("Mobile", key="reg_mobile")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

        if st.button("Register", key="submit_register"):
            if password != confirm:
                st.error("Passwords do not match")
            elif not mobile.isdigit() or len(mobile) != 10:
                st.error("Mobile must be 10 digits")
            elif add_user(name, email, company, mobile, password):
                st.success("Registration successful")
                st.session_state.account_page = "login"
                st.rerun()
            else:
                st.error("Email already exists")

        if st.button("Go Back", key="back_register"):
            reset_account_page()
            st.rerun()

    elif st.session_state.account_page == "forgot_password":
        st.subheader("Reset Password")
        email = st.text_input("Enter your registered email", key="reset_email")
        new_password = st.text_input("New Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")

        if st.button("Reset Password"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                update_password(email, new_password)
                st.success("Password updated successfully")
                st.session_state.account_page = "login"
                st.rerun()

        if st.button("Go Back", key="back_reset"):
            st.session_state.account_page = "login"
            st.rerun()

    elif st.session_state.account_page == "logged_in":
        st.success("Welcome to your dashboard!")
        st.write("More features coming soon...")
        if st.button("Logout", key="logout_btn"):
            reset_account_page()
            st.rerun()

# ---------- About Page ----------
elif st.session_state.nav_page == "About":
    st.title("About")
    st.markdown("This is a demo authentication platform built with Streamlit.")
