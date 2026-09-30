from navigation import home_page, recommender_page
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent


st.markdown('''<style>
.stApp {background:#fff8fb;color:#543744;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:1100px;padding-top:3rem;padding-bottom:2rem;}
h1 {letter-spacing:.025em;color:#6f4056 !important;font-size:2.35rem !important;}
h3 {color:#6f4056 !important;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff;border:1px solid #f0d8e3 !important;border-radius:20px !important;box-shadow:0 5px 20px #8f55700a;}
.card-icon {font-size:2rem;margin-bottom:.7rem;}
.card-copy {min-height:64px;color:#886a78;line-height:1.7;}
.eyebrow {color:#b47190;font-size:.85rem;letter-spacing:.14em;}
.footer {text-align:center;color:#a68494;font-size:.85rem;margin-top:2rem;line-height:1.9;}
a {color:#aa597f !important;}
[data-testid="stLinkButton"] a,[data-testid="stDownloadButton"] button {border-radius:10px;border:1px solid #e7bbce;background:#fff1f7;color:#88465f !important;}
</style>''', unsafe_allow_html=True)

def notebook_card(icon, title, description, filename, secret_key):
    with st.container(border=True):
        st.markdown(f'<div class="card-icon">{icon}</div>', unsafe_allow_html=True)
        st.subheader(title)
        st.markdown(f'<p class="card-copy">{description}</p>', unsafe_allow_html=True)
        default_urls = {
            "STRUCTURE_COLAB_URL": "https://colab.research.google.com/drive/1MLnfca_12xoU5Lx9DCyqn7-3nhfSfFC4?usp=sharing",
            "ANALYSIS_COLAB_URL": "https://colab.research.google.com/drive/1V-hcpVsOu7V6HUanrnRynK-WbW-sdQQB?usp=sharing",
        }
        url = default_urls[secret_key]
        try:
            url = st.secrets.get(secret_key, "") or url
        except st.errors.StreamlitSecretNotFoundError:
            pass
        if url and url.startswith("https://colab.research.google.com/"):
            st.link_button("เปิดระบบ →", url, use_container_width=True)
        else:
            st.caption("ดาวน์โหลดไฟล์ แล้วเปิดผ่าน Google Colab → อัปโหลด")
        st.download_button("ดาวน์โหลดโน้ตบุ๊ก ↓", (ROOT / "notebooks" / filename).read_bytes(), file_name=filename,
                           mime="application/x-ipynb+json", key=secret_key, use_container_width=True)

st.markdown('<div class="eyebrow">GRAPH · USERS · MOTORCYCLES</div>', unsafe_allow_html=True)
st.title("MOTORCYCLE RECOMMENDATION HUB")
st.write("ระบบแนะนำมอเตอร์ไซค์ด้วยกราฟความสัมพันธ์ระหว่าง User และ Motorcycle")
st.caption("🏍️ รวมโปรเจกต์ระบบแนะนำมอเตอร์ไซค์ของเรา")
st.divider()

left, right = st.columns(2, gap="large")
with left:
    notebook_card("🏍️", "โครงสร้างข้อมูล Motorcycle & User",
                  "สร้างกราฟผู้ใช้ 10 คน รถมอเตอร์ไซค์ 10 รุ่น และข้อมูลความชอบด้วย Python และ NetworkX",
                  "01_motorcycle_data_structure.ipynb", "STRUCTURE_COLAB_URL")
with right:
    notebook_card("👥", "วิเคราะห์ความสัมพันธ์ User",
                  "วิเคราะห์ความสัมพันธ์ LIKES ใน Neo4j และแนะนำรถจากผู้ใช้ที่ชอบรถรุ่นเดียวกัน",
                  "02_motorcycle_relationship_analysis.ipynb", "ANALYSIS_COLAB_URL")

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown('<div class="card-icon">🎯</div>', unsafe_allow_html=True)
        st.subheader("ระบบแนะนำมอเตอร์ไซค์")
        st.markdown('<p class="card-copy">เปิดเว็บระบบแนะนำมอเตอร์ไซค์ จัดการผู้ใช้และรถ พร้อมดูกราฟความสัมพันธ์</p>', unsafe_allow_html=True)
        if st.button("เปิดระบบ →", use_container_width=True):
            st.switch_page(recommender_page)
with right:
    with st.container(border=True):
        st.markdown('<div class="card-icon">🗄️</div>', unsafe_allow_html=True)
        st.subheader("Neo4j Database")
        st.markdown('<p class="card-copy">ฐานข้อมูลกราฟสำหรับจัดเก็บ User, Motorcycle และความสัมพันธ์ LIKES</p>', unsafe_allow_html=True)
        st.link_button("เปิดเว็บไซต์ →", "https://neo4j.com/", use_container_width=True)

st.markdown('<div class="footer">ผู้จัดทำ: ณัฏฐนันท์ เกียรติจิรยาดา · รหัสนักศึกษา 664245008<br>Made with ♡ using Streamlit · Motorcycle Recommendation System 2026</div>', unsafe_allow_html=True)
