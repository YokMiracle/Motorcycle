from pathlib import Path
import base64,io,json
from datetime import date
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import *

ROOT=Path(__file__).parent
st.set_page_config(page_title='Motorcycle Graph Recommendation',page_icon='🏍️',layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.2rem;max-width:1280px}.hero{padding:28px 32px;border-radius:24px;background:linear-gradient(135deg,#111827,#1f2937 55%,#374151);color:white;margin-bottom:18px}.hero h1{margin:0;color:white}.hero p{margin:7px 0 0;opacity:.82}.soft{padding:14px 18px;border:1px solid #e5e7eb;border-radius:18px;background:#fff}.stButton>button{border-radius:12px}[data-testid="stMetric"]{border:1px solid #e5e7eb;padding:15px;border-radius:16px;background:white}</style>''',unsafe_allow_html=True)

with st.sidebar:
    if (ROOT/'img.jpg').exists(): st.image(str(ROOT/'img.jpg'),width=130)
    st.title('🏍️ MotoGraph')
    page=st.radio('เมนู',['หน้าหลัก','แนะนำรถสำหรับคุณ','บันทึกการเช่าและให้คะแนน','ประวัติการเช่า','กราฟความสัมพันธ์','จัดการข้อมูล'])
    st.caption('Graph-based Recommendation · Neo4j')

st.markdown('<div class="hero"><h1>Motorcycle Graph Recommendation</h1><p>แนะนำรถจากความสัมพันธ์ระหว่างผู้ใช้ ประวัติการเช่า และคะแนนความพึงพอใจ</p></div>',unsafe_allow_html=True)
try: query('RETURN 1 AS ok')
except Exception:
    st.error('ยังเชื่อมต่อ Neo4j ไม่ได้ กรุณาตั้งค่า Secrets ตาม README'); st.stop()

if not users() or not models():
    st.warning('ยังไม่มีข้อมูลเริ่มต้น')
    if st.button('สร้างข้อมูลรถและผู้ใช้เดิม',type='primary'): seed_demo_data(); st.rerun()
    st.stop()

def show_image(row):
    try:
        if row.get('image_data'): st.image(base64.b64decode(row['image_data']),use_container_width=True)
        elif row.get('image_url'): st.image(row['image_url'],use_container_width=True)
        else: st.image(str(ROOT/'assets'/'placeholder.png'),use_container_width=True)
    except: st.image(str(ROOT/'assets'/'placeholder.png'),use_container_width=True)

def user_picker(key): return st.selectbox('เลือกผู้ใช้',users(),key=key)
def cards(rows,reco=False):
    if not rows: st.info('ยังไม่มีรายการ'); return
    cols=st.columns(3)
    for i,r in enumerate(rows):
        with cols[i%3]:
            with st.container(border=True):
                show_image(r); st.subheader(r['name'])
                if reco:
                    st.write(f"⭐ {r['avg_rating']:.2f}/5 · {r['rating_count']} คะแนน")
                    st.progress(min(float(r['score'])/12,1.0),text=f"คะแนนแนะนำ {r['score']:.2f}")
                    if r['similar_users']: st.caption('ผู้ใช้ที่มีพฤติกรรมคล้ายกัน: '+', '.join(r['similar_users']))
                    if r['shared_models']: st.caption('เชื่อมโยงผ่านรถที่เคยเช่าเหมือนกัน: '+', '.join(r['shared_models']))

if page=='หน้าหลัก':
    edges=graph_edges(); u=user_picker('home_user')
    a,b,c,d=st.columns(4); a.metric('ผู้ใช้',len(users())); b.metric('รถทั้งหมด',len(models())); c.metric('ความสัมพันธ์ RENTED',len(edges)); d.metric('คะแนนเฉลี่ย',f"{sum(float(x['rating']) for x in edges if x['rating'] is not None)/max(1,len([x for x in edges if x['rating'] is not None])):.2f}/5")
    st.divider(); left,right=st.columns([1,2])
    h=rental_history(u)
    with left:
        st.subheader(f'👤 {u}'); st.metric('จำนวนครั้งที่เช่า',len(h)); st.metric('รุ่นที่เคยเช่า',len(set(x['name'] for x in h)))
    with right:
        st.subheader('กิจกรรมล่าสุด'); st.dataframe(pd.DataFrame(h),hide_index=True,use_container_width=True)
    st.subheader('รถที่เคยเช่า'); cards(liked(u))

elif page=='แนะนำรถสำหรับคุณ':
    u=user_picker('recommend_user'); st.caption('ระบบหาเพื่อนผู้ใช้ที่เคยเช่ารถเหมือนกัน แล้วนำรถที่คนเหล่านั้นชอบแต่คุณยังไม่เคยเช่ามาจัดอันดับ')
    n=st.slider('จำนวนคำแนะนำ',1,10,6); result=recommend(u,n)
    st.subheader(f'✨ แนะนำสำหรับ {u}'); cards(result,True)
    if not result: st.info('ผู้ใช้นี้ยังมีข้อมูลเชื่อมโยงไม่พอ ลองบันทึกการเช่า/คะแนนเพิ่ม')

elif page=='บันทึกการเช่าและให้คะแนน':
    u=user_picker('rate_user'); rows=catalog(); m=st.selectbox('เลือกรถที่เคยเช่า',[x['name'] for x in rows]); show_image(next(x for x in rows if x['name']==m))
    with st.form('rating'):
        d=st.date_input('วันที่เช่า',date.today(),max_value=date.today()); rating=st.slider('คะแนนความพึงพอใจ',1.0,5.0,4.0,.5)
        if st.form_submit_button('บันทึก',type='primary'):
            record_rental(u,m,d.isoformat(),rating); st.success('บันทึกความสัมพันธ์ RENTED และคะแนนแล้ว'); st.rerun()

elif page=='ประวัติการเช่า':
    u=user_picker('history_user'); h=rental_history(u); st.subheader(f'ประวัติของ {u}')
    if h: st.dataframe(pd.DataFrame(h),hide_index=True,use_container_width=True)
    else: st.info('ยังไม่มีประวัติการเช่า')

elif page=='กราฟความสัมพันธ์':
    mode=st.radio('ขอบเขตกราฟ',['เฉพาะผู้ใช้','ผู้ใช้ทั้งหมด'],horizontal=True)
    u=user_picker('graph_user') if mode=='เฉพาะผู้ใช้' else None; edges=graph_edges(u)
    dot=['digraph G {','rankdir=LR;','graph [bgcolor="transparent"];','node [fontname="Arial"];']
    for e in edges:
        uid='u:'+e['user']; mid='m:'+e['motorcycle'];
        dot += [f'{json.dumps(uid)} [label={json.dumps(e["user"])} shape=ellipse style=filled fillcolor="#DBEAFE"];',f'{json.dumps(mid)} [label={json.dumps(e["motorcycle"])} shape=box style="rounded,filled" fillcolor="#F3F4F6"];',f'{json.dumps(uid)} -> {json.dumps(mid)} [label={json.dumps("RENTED · "+str(e["rating"] if e["rating"] is not None else "-"))}];']
    st.graphviz_chart('\n'.join(dot+['}']),use_container_width=True); st.dataframe(pd.DataFrame(edges),hide_index=True,use_container_width=True)

elif page=='จัดการข้อมูล':
    tab1,tab2,tab3=st.tabs(['เพิ่มรถ','เพิ่มผู้ใช้','แก้ไขรูปรถ'])
    with tab1:
        st.subheader('เพิ่มรถใหม่เข้ากราฟ')
        name=st.text_input('ชื่อรถใหม่'); upload=st.file_uploader('รูปรถ',type=['jpg','jpeg','png','webp'],key='newcar'); url=st.text_input('หรือ URL รูปภาพ https://',key='newurl')
        if st.button('เพิ่มรถ',type='primary'):
            data=''
            if upload:
                im=Image.open(upload).convert('RGB'); im.thumbnail((1200,900)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=88); data=base64.b64encode(buf.getvalue()).decode()
            if url and not (urlparse(url).scheme=='https' and urlparse(url).netloc): st.error('URL ต้องเป็น https://')
            else: add_motorcycle(name,url.strip(),data); st.success('เพิ่มรถแล้ว รถจะปรากฏในทุกหน้าของระบบ'); st.rerun()
    with tab2:
        newuser=st.text_input('ชื่อผู้ใช้ใหม่')
        if st.button('เพิ่มผู้ใช้'): add_user(newuser); st.success('เพิ่มผู้ใช้แล้ว'); st.rerun()
    with tab3:
        rows=catalog(); m=st.selectbox('เลือกรถ',[x['name'] for x in rows],key='editcar'); row=next(x for x in rows if x['name']==m); show_image(row)
        upload=st.file_uploader('เปลี่ยนรูป',type=['jpg','jpeg','png','webp'],key='editimg'); url=st.text_input('หรือ URL ใหม่',value=row.get('image_url') or '',key='editurl')
        if st.button('บันทึกรูป'):
            data=row.get('image_data') or ''
            if upload:
                im=Image.open(upload).convert('RGB'); im.thumbnail((1200,900)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=88); data=base64.b64encode(buf.getvalue()).decode(); url=''
            save_image(m,url.strip(),data); st.success('บันทึกแล้ว'); st.rerun()
