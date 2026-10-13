import streamlit as st
import pandas as pd
import requests
from io import StringIO

API_URL = "http://localhost:8000"

REQUIRED_COLUMNS = ["name", "class_level", "house_number", "contact", "joining_date"]

def render_csv_import():
    st.subheader("📥 Import Students from CSV")

    with st.expander("❓ CSV Format Guidelines"):
        st.markdown("""
        - **Required Columns:**  
            `name`, `class_level`, `house_number`, `contact`, `joining_date`  
        - **Optional Columns:**  
            `parent_name`, `parent_relation`, `parent_contact`, `parent_email`  
        - **Date Format:**  
            `joining_date` should be in `YYYY-MM-DD` format.
        """)

    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
    if not uploaded:
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"❌ Failed to read CSV file: {e}")
        return

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return

    if df.empty:
        st.warning("⚠️ Uploaded CSV is empty.")
        return

    st.markdown("#### 📄 Preview of Uploaded Data")
    st.dataframe(df.head())

    if st.button("✅ Confirm Import"):
        try:
            uploaded.seek(0)  # Reset file pointer
            files = {"file": (uploaded.name, uploaded, "text/csv")}
            response = requests.post(f"{API_URL}/students/import_csv", files=files)

            if response.ok:
                imported = response.json().get("imported", 0)
                st.success(f"✅ Successfully imported {imported} students!")
            else:
                st.error(f"❌ Import failed. {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request error: {e}")
        except Exception as ex:
            st.error(f"❌ Unexpected error: {ex}")
