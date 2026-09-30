from navigation import recommender_page
import streamlit as st

st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 50% 0%,#fce8ef 0%,#fff7fa 45%,#fffafa 100%);color:#654b56}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1160px;padding:3.5rem 2rem 2rem}
.hub-hero{text-align:center;padding:1.8rem 1rem 2.8rem}
.hub-badge{display:inline-block;padding:8px 18px;border:1px solid #ecd3df;border-radius:30px;font-size:11px;letter-spacing:.18em;color:#a16c83;background:#fff9fc}
.hub-hero h1{font-size:clamp(30px,4vw,46px);line-height:1.3;font-weight:650;color:#795365;letter-spacing:-.025em;margin:22px 0 16px;padding:0}
.hub-hero p{font-size:16px;color:#947986;line-height:1.9;margin:0}
.hub-section{text-align:center;margin:0 0 22px;color:#a27e90;font-size:13px;letter-spacing:.025em}
.st-key-structure,.st-key-analysis,.st-key-recommendation{background:#fffcfd;border:1px solid #efdee6!important;border-radius:24px!important;padding:26px!important;box-shadow:0 12px 35px #a16c8309;transition:transform .2s,box-shadow .2s}
.st-key-structure:hover,.st-key-analysis:hover,.st-key-recommendation:hover{transform:translateY(-3px);box-shadow:0 16px 36px #a16c8314}
.hub-card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:26px}
.hub-icon{width:54px;height:54px;border-radius:17px;background:#f9eaf0;display:flex;align-items:center;justify-content:center;color:#b47a95}
.hub-icon svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.hub-number{color:#c7aeba;font-size:12px;letter-spacing:.08em}
.hub-card-title{color:#775565;font-size:21px;font-weight:600;line-height:1.6;margin:0 0 10px}
.hub-card-copy{font-size:14px;line-height:1.9;color:#9a7f8d;min-height:82px;margin:0 0 20px}
[data-testid="stLinkButton"] a,[data-testid="stButton"] button{border:1px solid #ecd0dd!important;border-radius:12px!important;background:#f9e8f0!important;color:#95617b!important;font-size:14px;min-height:46px;box-shadow:none!important}
[data-testid="stLinkButton"] a:hover,[data-testid="stButton"] button:hover{background:#f4dce7!important;border-color:#dcb3c6!important}
.hub-footer{border-top:1px solid #ecdde4;margin-top:42px;padding-top:24px;text-align:center;color:#a58a97;font-size:12px;line-height:2}
.hub-footer strong{font-weight:500;color:#8d6a7d}
@media(max-width:760px){.block-container{padding:2rem 1rem}.hub-hero{padding:.8rem 0 2rem}.hub-hero p{font-size:14px}.hub-card-copy{min-height:0}.hub-hero h1{font-size:31px}}
@media(prefers-reduced-motion:reduce){.st-key-structure,.st-key-analysis,.st-key-recommendation{transition:none}.st-key-structure:hover,.st-key-analysis:hover,.st-key-recommendation:hover{transform:none}}
</style>''', unsafe_allow_html=True)

URLS = {
    'STRUCTURE_COLAB_URL': 'https://colab.research.google.com/drive/1MLnfca_12xoU5Lx9DCyqn7-3nhfSfFC4?usp=sharing',
    'ANALYSIS_COLAB_URL': 'https://colab.research.google.com/drive/1V-hcpVsOu7V6HUanrnRynK-WbW-sdQQB?usp=sharing',
}

def colab_url(key):
    try:
        value = st.secrets.get(key, '')
    except st.errors.StreamlitSecretNotFoundError:
        value = ''
    return value if value.startswith('https://colab.research.google.com/') else URLS[key]

ICONS = {
    'structure': '<rect x="4" y="3" width="16" height="6" rx="2"/><rect x="4" y="15" width="6" height="6" rx="2"/><rect x="14" y="15" width="6" height="6" rx="2"/><path d="M12 9v3M7 15v-3h10v3"/>',
    'analysis': '<circle cx="6" cy="6" r="3"/><circle cx="18" cy="8" r="3"/><circle cx="10" cy="19" r="3"/><path d="m9 6 6 1M7 9l2 7m7-5-4 5"/>',
    'recommendation': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="m10 12 2 2 4-5"/>',
}

def card_heading(kind, number, title, copy):
    st.markdown(f'''<div class="hub-card-top"><div class="hub-icon"><svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[kind]}</svg></div><span class="hub-number">{number}</span></div><h2 class="hub-card-title">{title}</h2><p class="hub-card-copy">{copy}</p>''', unsafe_allow_html=True)

st.markdown('''<div class="hub-hero"><span class="hub-badge">MOTORCYCLE · RECOMMENDATION HUB</span><h1>ค้นพบมอเตอร์ไซค์<br>ที่ใช่สำหรับคุณ</h1><p>เชื่อมโยงความชอบ สู่มอเตอร์ไซค์ที่น่าสนใจ<br>รวมโครงสร้างข้อมูล การวิเคราะห์ และระบบแนะนำไว้ในที่เดียว</p></div><div class="hub-section">เลือกส่วนของโปรเจกต์ที่ต้องการสำรวจ</div>''', unsafe_allow_html=True)

columns = st.columns(3, gap='medium')
with columns[0], st.container(border=True, key='structure'):
    card_heading('structure', '01 / DATA', 'โครงสร้างข้อมูล', 'สำรวจข้อมูลผู้ใช้และมอเตอร์ไซค์<br>พร้อมแนวทางสร้างกราฟ<br>เพื่อเชื่อมโยงความชอบของแต่ละคน')
    st.link_button('เปิดโครงสร้างข้อมูล ↗', colab_url('STRUCTURE_COLAB_URL'), use_container_width=True)
with columns[1], st.container(border=True, key='analysis'):
    card_heading('analysis', '02 / CONNECTIONS', 'วิเคราะห์ความสัมพันธ์', 'ค้นหาผู้ใช้ที่มีความชอบคล้ายกัน<br>และสำรวจความเชื่อมโยง<br>ที่นำไปสู่คำแนะนำใหม่ ๆ')
    st.link_button('เปิดการวิเคราะห์ ↗', colab_url('ANALYSIS_COLAB_URL'), use_container_width=True)
with columns[2], st.container(border=True, key='recommendation'):
    card_heading('recommendation', '03 / DISCOVER', 'แนะนำมอเตอร์ไซค์', 'ลองค้นหามอเตอร์ไซค์ที่น่าสนใจ<br>จัดการข้อมูลผู้ใช้และรถ<br>พร้อมสำรวจกราฟความสัมพันธ์')
    if st.button('เข้าสู่ระบบแนะนำ →', use_container_width=True):
        st.switch_page(recommender_page)

st.markdown('''<div class="hub-footer"><strong>ณัฏฐนันท์ เกียรติจิรยาดา</strong> · รหัสนักศึกษา 664245008<br>Motorcycle Recommendation Project · 2026</div>''', unsafe_allow_html=True)
