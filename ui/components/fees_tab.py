# ui/components/fees_tab.py

import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px

BASE_URL = "http://localhost:8000"

def display():
    st.subheader("💰 Tuition Fee Dashboard")

    # ----------------------------------
    # Fetch Students
    # ----------------------------------
    try:
        students_resp = requests.get(f"{BASE_URL}/students/?include_frozen=false")
        students_resp.raise_for_status()
        students = students_resp.json()
    except:
        st.error("❌ Failed to fetch students.")
        return

    if not students:
        st.warning("No active students found.")
        return

    student_dict = {s["id"]: s for s in students}
    student_options = {f"{s['name']} (Class {s['class_level']})": s["id"] for s in students}
    selected_name = st.selectbox("Select Student", list(student_options.keys()))
    student_id = student_options[selected_name]

    # ----------------------------------
    # Fetch Fee Summary
    # ----------------------------------
    try:
        summary = requests.get(f"{BASE_URL}/fees/{student_id}/summary").json()
        config = requests.get(f"{BASE_URL}/fees/config/{student_id}").json()
    except:
        st.error("❌ Failed to fetch fee data.")
        return

    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("Monthly Fee", f"₹{config['monthly_fee']}")
        col2.metric("Total Paid", f"₹{summary['paid']}")
        col3.metric("Total Due", f"₹{summary['due']}")

    # ----------------------------------
    # Payment History
    # ----------------------------------
    st.markdown("### 📜 Payment History")
    try:
        records = requests.get(f"{BASE_URL}/fees/{student_id}/records").json()
        if records:
            df = pd.DataFrame(records)
            df["payment_date"] = pd.to_datetime(df["payment_date"]).dt.date
            st.dataframe(df[["receipt_number", "payment_date", "amount_paid", "method", "note"]], use_container_width=True)
        else:
            st.info("No payment records found.")
    except:
        st.error("Failed to load fee records.")

    # ----------------------------------
    # Add Payment Form
    # ----------------------------------
    st.markdown("### ➕ Add New Payment")

    with st.form("add_payment_form"):
        amount = st.number_input("Amount Paid", min_value=0.0, step=10.0, format="%.2f")
        payment_date = st.date_input("Payment Date", value=date.today())
        method = st.selectbox("Payment Method", ["Cash", "UPI", "Bank Transfer"])
        receipt_number = st.text_input("Receipt Number")
        note = st.text_area("Note (optional)", height=60)
        submit_btn = st.form_submit_button("💾 Record Payment")

    if submit_btn:
        if not receipt_number.strip():
            st.warning("Receipt number is required.")
        else:
            payload = {
                "student_id": student_id,
                "amount_paid": amount,
                "payment_date": str(payment_date),
                "method": method,
                "receipt_number": receipt_number,
                "note": note
            }
            try:
                res = requests.post(f"{BASE_URL}/fees/pay", json=payload)
                if res.status_code == 200:
                    st.success("Payment recorded successfully.")
                    st.experimental_rerun()
                else:
                    st.error(f"Failed to save payment: {res.text}")
            except:
                st.error("Error while saving payment.")

    # ----------------------------------
    # Export All Receipts (CSV)
    # ----------------------------------
    st.markdown("### 📤 Export All Receipts")
    if st.button("⬇️ Download CSV"):
        try:
            all_records = requests.get(f"{BASE_URL}/fees/all").json()
            if not all_records:
                st.warning("No records to export.")
            else:
                df_all = pd.DataFrame(all_records)
                df_all["payment_date"] = pd.to_datetime(df_all["payment_date"]).dt.date
                csv = df_all.to_csv(index=False).encode('utf-8')
                st.download_button("Download Receipts CSV", data=csv, file_name="fee_receipts.csv", mime="text/csv")
        except:
            st.error("Export failed.")

    # ----------------------------------
    # Class-wise Due Report
    # ----------------------------------
    st.markdown("### 📊 Class-wise Dues Summary")
    class_levels = sorted(set(s["class_level"] for s in students))
    selected_class = st.selectbox("Select Class", class_levels)

    try:
        dues = requests.get(f"{BASE_URL}/fees/dues/{selected_class}").json()
        if dues:
            df_due = pd.DataFrame(dues)
            df_due["Due"] = df_due["due_amount"]
            fig = px.bar(df_due, x="name", y="Due", title=f"Outstanding Dues - Class {selected_class}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No dues found in this class.")
    except:
        st.error("Could not load class-wise dues.")

