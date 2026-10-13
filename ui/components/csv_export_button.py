# ui/components/csv_export_button.py

import streamlit as st
import pandas as pd
import io

def download_students_csv(student_list):
    if not student_list:
        st.warning("⚠️ No students available to export.")
        return

    df = pd.DataFrame(student_list)

    # Convert to CSV
    csv = df.to_csv(index=False)
    buffer = io.BytesIO()
    buffer.write(csv.encode('utf-8'))
    buffer.seek(0)

    st.download_button(
        label="📥 Download Students CSV",
        data=buffer,
        file_name="students_export.csv",
        mime="text/csv"
    )
