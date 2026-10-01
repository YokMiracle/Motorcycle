from pathlib import Path
import html
import streamlit as st
from navigation import recommender_page

ROOT = Path(__file__).resolve().parent
REPOSITORY = "https://github.com/YokMiracle/Motorcycle"

st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 50% 0%,#fce8ef 0%,#fff7fa 45%,#fffafa 100%);color:#654b56}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1600px;padding:2rem 2rem}
.hub-hero{text-align:center;padding:.5rem 0 1rem}
.hub-badge{display:inline-block;padding:7px 18px;border:1px solid #ecd3df;border-radius:30px;font-size:11px;letter-spacing:.16em;color:#a16c83;background:#fff9fc}
.hub-hero h1{font-size:clamp(28px,4vw,42px);line-height:1.4;font-weight:650;color:#795365;margin:14px 0 8px;padding:0}
.hub-hero p{font-size:15px;color:#947986;line-height:1.8;margin:0}
.st-key-club,.st-key-graph,.st-key-neo4j,.st-key-recommendation{background:#fffcfd;border:1px solid #efdee6!important;border-radius:22px!important;padding:20px!important;box-shadow:0 10px 30px #a16c8309;box-sizing:border-box!important}
.hub-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.hub-icon{width:44px;height:44px;border-radius:14px;background:#f9eaf0;display:flex;align-items:center;justify-content:center;color:#b47a95}
.hub-icon svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.hub-number{color:#b795a6;font-size:12px;letter-spacing:.06em}
.hub-card-title{min-height:68px;color:#775565;font-size:21px;font-weight:600;line-height:1.6;margin:0 0 6px}
.hub-card-copy{color:#947986;font-size:14px;line-height:1.8;margin:0;min-height:101px}
.st-key-club>[data-testid="stVerticalBlock"],.st-key-graph>[data-testid="stVerticalBlock"],.st-key-neo4j>[data-testid="stVerticalBlock"],.st-key-recommendation>[data-testid="stVerticalBlock"]{min-height:340px;justify-content:space-between}
[data-testid="stLinkButton"] a,[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{border:1px solid #ecd0dd!important;border-radius:12px!important;background:#f9e8f0!important;color:#95617b!important;font-size:14px;min-height:44px;box-shadow:none!important}
[data-testid="stLinkButton"] a:hover,[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{background:#f4dce7!important;border-color:#dcb3c6!important}
.hub-footer{border-top:1px solid #ecdde4;margin-top:24px;padding-top:18px;text-align:center;color:#a58a97;font-size:12px;line-height:1.8}
@media(max-width:760px){.block-container{padding:1.5rem 1rem}.hub-hero h1{font-size:29px}.hub-card-title{font-size:20px}}
</style>''', unsafe_allow_html=True)

ICONS = {
    "club": '<circle cx="9" cy="7" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5"/>',
    "graph": '<rect x="4" y="3" width="16" height="6" rx="2"/><rect x="4" y="15" width="6" height="6" rx="2"/><rect x="14" y="15" width="6" height="6" rx="2"/><path d="M12 9v3M7 15v-3h10v3"/>',
    "neo4j": '<circle cx="6" cy="6" r="3"/><circle cx="18" cy="8" r="3"/><circle cx="10" cy="19" r="3"/><path d="m9 6 6 1M7 9l2 7m7-5-4 5"/>',
    "recommendation": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="m10 12 2 2 4-5"/>',
}

def heading(kind, number, title, copy):
    st.markdown(f'''<div class="hub-top"><div class="hub-icon"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[kind]}</svg></div><span class="hub-number">{number}</span></div><div class="hub-card-title" role="heading" aria-level="2">{html.escape(title)}</div><p class="hub-card-copy">{html.escape(copy)}</p>''', unsafe_allow_html=True)

def notebook_actions(path):
    st.link_button("เปิดการบ้านใน Colab ↗", f"https://colab.research.google.com/github/YokMiracle/Motorcycle/blob/main/{path}", use_container_width=True)
    st.link_button("ดูไฟล์บน GitHub ↗", f"{REPOSITORY}/blob/main/{path}", use_container_width=True)

st.markdown('''<div class="hub-hero"><span class="hub-badge">HOMEWORK · RECOMMENDATION HUB</span><h1>รวมการบ้านและระบบแนะนำ</h1><p>ระบบชมรม · กราฟมอเตอร์ไซค์ · Neo4j<br>เลือกงานที่ต้องการเปิดดูได้จากการ์ดด้านล่าง</p></div>''', unsafe_allow_html=True)

columns = st.columns(4, gap="medium")
with columns[0], st.container(border=True, height=400, key="club"):
    heading("club", "01 / CLUB", "ระบบชมรมด้วย Neo4j", "งานระบบชมรม: นักศึกษา ชมรม ความสัมพันธ์ และคำสั่ง Cypher พร้อมเอกสาร PDF")
    with st.container():
        st.link_button("เปิดการบ้านบน GitHub ↗", f"{REPOSITORY}/blob/main/homework/664245008_club_system.pdf", use_container_width=True)
        st.download_button("ดาวน์โหลดเอกสาร PDF ↓", (ROOT / "homework/664245008_club_system.pdf").read_bytes(), file_name="664245008_club_system.pdf", mime="application/pdf", use_container_width=True)
with columns[1], st.container(border=True, height=400, key="graph"):
    heading("graph", "02 / GRAPH", "มอเตอร์ไซค์ด้วย Graph", "สร้างกราฟผู้ใช้และมอเตอร์ไซค์ด้วย Python / NetworkX เพื่อสำรวจความชอบและแนวทางแนะนำ")
    with st.container():
        notebook_actions("homework/664245008_Motorcycle_RecommenderSystem.ipynb")

with columns[2], st.container(border=True, height=400, key="neo4j"):
    heading("neo4j", "03 / NEO4J", "มอเตอร์ไซค์ด้วย Neo4j", "วิเคราะห์ความสัมพันธ์และแนะนำมอเตอร์ไซค์ด้วย Neo4j จากไฟล์การบ้าน CryptoRecommender ที่แนบมา")
    with st.container():
        notebook_actions("homework/CryptoRecommender_664245008_Neo4j.ipynb")
with columns[3], st.container(border=True, height=400, key="recommendation"):
    heading("recommendation", "04 / APPLICATION", "ระบบแนะนำมอเตอร์ไซค์", "ทดลองระบบแนะนำ เลือกผู้ใช้ จัดการข้อมูลรถ และสำรวจกราฟความสัมพันธ์ภายในแอป")
    with st.container():
        if st.button("เข้าสู่ระบบแนะนำ →", use_container_width=True):
            st.switch_page(recommender_page)
        st.link_button("ดูโค้ดโปรเจกต์บน GitHub ↗", REPOSITORY, use_container_width=True)

st.markdown('''<div class="hub-footer">ณัฏฐนันท์ เกียรติจิรยาดา · รหัสนักศึกษา 664245008<br>Motorcycle Recommendation Project</div>''', unsafe_allow_html=True)
