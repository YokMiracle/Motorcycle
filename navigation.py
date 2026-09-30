import streamlit as st

home_page = st.Page("hub_page.py", title="หน้ารวมโปรเจกต์", icon="🏍️", default=True)
recommender_page = st.Page("recommender_page.py", title="ระบบแนะนำมอเตอร์ไซค์", icon="🎯", url_path="recommendation")
