import streamlit as st
import streamlit.components.v1 as components

def display():
    st.subheader("📊 TuitorIN – Interactive Dashboard (Powered by Power BI)")

    st.markdown("""
        This dashboard showcases insights into student performance, attendance trends, task completion, and overall tuition operations — all powered by Microsoft Power BI.
    """)

    # 🔗 Replace with your actual published Power BI public URL
    powerbi_embed_url = st.secrets.get("POWERBI_EMBED_URL", "")

    if not powerbi_embed_url or powerbi_embed_url == "https://app.powerbi.com/view?r=YOUR_PUBLIC_LINK":
        st.warning("🔗 Power BI dashboard URL not configured yet.")
        st.info("You can host the `.pbix` file on Power BI Service and paste the public embed URL here.")
        powerbi_embed_url = st.text_input("Paste Power BI embed URL to preview it below:")

    if powerbi_embed_url:
        components.iframe(src=powerbi_embed_url, width=1100, height=650, scrolling=True)
