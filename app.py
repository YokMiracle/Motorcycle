import streamlit as st

st.set_page_config(page_title="Motorcycle Recommendation Hub", page_icon="🏍️", layout="wide")
from navigation import home_page, recommender_page
st.navigation([home_page, recommender_page], position="hidden").run()
