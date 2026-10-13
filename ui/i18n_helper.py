# ui/i18n_helper.py

import streamlit as st
import yaml
import os

# ✅ Cache translation files efficiently
@st.cache_data
def load_translation(lang: str) -> dict:
    """Load language YAML file based on selected language code."""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "i18n", f"{lang}.yaml"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

# ✅ Internal cache to prevent redundant file reads in the same session
_translation_cache = {}

def _(key: str) -> str:
    """Translate a given key to the selected language."""
    lang = st.session_state.get("lang", "en")  # Use 'lang' to match streamlit_app.py
    if lang not in _translation_cache:
        _translation_cache[lang] = load_translation(lang)
    return _translation_cache[lang].get(key, key)  # Fallback to key itself if not found
