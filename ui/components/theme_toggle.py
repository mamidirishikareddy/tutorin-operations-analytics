# ui/components/theme_toggle.py

import streamlit as st

def apply_theme():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Light"

    theme = st.sidebar.radio("🌓 Theme Mode", ["Light", "Dark"], index=0 if st.session_state.theme_mode == "Light" else 1)
    st.session_state.theme_mode = theme

    if theme == "Dark":
        st.markdown("""
        <style>
            html, body, .stApp {
                background-color: #111 !important;
                color: #f0f0f0 !important;
            }
            .st-bk, .css-ffhzg2, .css-1d391kg {
                background-color: #1e1e1e !important;
            }
            .st-cg {
                color: #f0f0f0 !important;
            }
            .css-1cpxqw2, .stMarkdown, .stDataFrame, .stTextInput>div>input {
                color: white !important;
                background-color: #1e1e1e !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Optional: reset or inject light mode CSS if needed
        pass