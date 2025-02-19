import streamlit as st

def show_login_warning():
    st.warning("⚠️ Please log in to access this feature")
    google_button = st.button("Google Login")
    if google_button:
        st.login(provider="google")
    

def require_auth(content_function):
    """Decorator to require authentication before showing content"""
    if not st.experimental_user.is_logged_in:
        show_login_warning()
        return
    
    if st.experimental_user.email not in st.secrets["auth"]["allowed_emails"]:
        st.error("Unauthorized email address")
        return
        
    content_function()
