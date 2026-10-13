import streamlit as st
from app.db import get_session
from app.models import ToDoItem
from sqlalchemy import func

def notification_bell():
    session = get_session()
    try:
        pending_count = session.query(func.count(ToDoItem.id)).filter(ToDoItem.is_done == False).scalar() or 0

        if pending_count > 0:
            st.markdown(f"""
            <div style="position: fixed; top: 1.2rem; right: 2rem; z-index: 1000;">
                <span style="background-color: red; color: white; border-radius: 50%;
                    padding: 0.25rem 0.5rem; font-size: 0.75rem; position: absolute; top: -10px; right: -10px;">
                    {pending_count}
                </span>
                <span style="font-size: 1.5rem;">🔔</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="position: fixed; top: 1.2rem; right: 2rem; z-index: 1000;">
                <span style="font-size: 1.5rem; color: gray;">🔕</span>
            </div>
            """, unsafe_allow_html=True)

    finally:
        session.close()
