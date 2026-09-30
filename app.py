from pathlib import Path
import base64, io, json
from datetime import date
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import *

ROOT=Path(__file__).parent
st.set_page_config(page_title='MotoGraph Recommendation',page_icon='🏍️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
:root{--ink:#172033;--muted:#6b7280;--line:#e8eaf0;--soft:#f7f8fb;--accent:#ff6b6b}
.block-container{padding-top:1.25rem;max-width:1320px}.hero{padding:30px 34px;border-radius:26px;background:linear-gradient(135deg,#171923,#252b3b 58%,#384152);color:#fff;margin-bottom:20px;box-shadow:0 16px 45px #11182718}.hero h1{margin:0;color:#fff;font-size:2.15rem}.hero p{margin:.5rem 0 0;color:#d8dce6}.section{font-weight:750;font-size:1.35rem;margin:8px 0 12px}.muted{color:#6b7280}.pill{display:inline-block;padding:5px 10px;border-radius:999px;background:#f1f3f7;font-size:.82rem;color:#4b5563;margin-right:5px}.stButton>button{border-radius:12px;font-weight:650}[data-testid="stMetric"]{border:1px solid #e8eaf0;padding:15px;border-radius:18px;background:#fff;box-shadow:0 4px 18px #11182708}[data-testid="stSidebar"]{border-right:1px solid #eceef3}.motor-card{border:1px solid #e8eaf0;border-radius:18px;padding:10px;background:#fff}.stDataFrame{border:1px solid #eceef3;border-radius:14px;overflow:hidden}</style>''',unsafe_allow_html=True)

MENU=['ภาพรวม','แนะนำสำหรับคุณ','บันทึกความชอบ','ประวัติความชอบ','กราฟความสัมพันธ์','จัดการข้อมูล']
with st.sidebar:
    if (ROOT/'img.jpg').exists(): st.image(str(ROOT/'img.jpg'),width=120)
    st.title('MotoGraph')
    st.caption('Motorcycle Recommendation System')
    page=st.radio('เมนูหลัก',MENU,label_visibility='collapsed')
    st.divider(); st.caption('Neo4j · Graph Recommendation · Streamlit')

st.markdown('<div class="hero"><h1>🏍️ Motorcycle Graph Recommendation</h1><p>ระบบแนะนำมอเตอร์ไซค์จากความชอบของผู้ใช้และความสัมพันธ์ในกราฟ</p></div>',unsafe_allow_html=True)

try:
    query('RETURN 1 AS ok')
except Exception as e:
    st.error('ยังเชื่อมต่อ Neo4j ไม่ได้ กรุณาตั้งค่า .streamlit/secrets.toml ตาม README')
    st.code(str(e)); st.stop()

if not users() or not models():
    st.info('ฐานข้อมูลยังว่าง กดปุ่มด้านล่างเพื่อสร้างข้อมูลมอเตอร์ไซค์เดิมของโปรเจกต์')
    if st.button('สร้างข้อมูลเริ่มต้น',type='primary'):
        setup_data(); st.rerun()
    st.stop()
else:
    # Safe idempotent migration: keeps old RENTED data while switching app semantics to LIKES.
    try: setup_data()
    except Exception: pass

def show_image(row, height=None):
    try:
        if row.get('image_data'): st.image(base64.b64decode(row['image_data']),use_container_width=True)
        elif row.get('image_url'): st.image(row['image_url'],use_container_width=True)
        else: st.image(str(ROOT/'assets'/'placeholder.png'),use_container_width=True)
    except Exception: st.image(str(ROOT/'assets'/'placeholder.png'),use_container_width=True)

def user_picker(key,label='เลือกผู้ใช้'):
    return st.selectbox(label,users(),key=key)

def motorcycle_cards(rows,recommendation=False):
    if not rows: st.info('ยังไม่มีข้อมูลที่จะแสดง'); return
    cols=st.columns(3)
    for i,r in enumerate(rows):
        with cols[i%3]:
            with st.container(border=True):
                show_image(r); st.subheader(r['name'])
                if recommendation:
                    st.write(f"⭐ {float(r.get('avg_rating',0)):.1f}/5  ·  ❤️ {int(r.get('like_count',0))} คนชอบ")
                    st.progress(min(float(r.get('score',0))/15,1.0),text=f"Recommendation score {float(r.get('score',0)):.2f}")
                    if r.get('similar_users'): st.caption('ผู้ใช้ที่ชอบคล้ายกัน: '+', '.join(r['similar_users']))
                    if r.get('shared_models'): st.caption('เชื่อมโยงจากรถที่ชอบเหมือนกัน: '+', '.join(r['shared_models']))
                else:
                    if 'like_count' in r: st.caption(f"❤️ {int(r.get('like_count',0))} ความชอบ · ⭐ {float(r.get('avg_rating',0)):.1f}")

def dataframe(rows, columns=None):
    df=pd.DataFrame(rows)
    if columns and not df.empty: df=df.rename(columns=columns)
    st.dataframe(df,hide_index=True,use_container_width=True)

if page=='ภาพรวม':
    u=user_picker('overview_user')
    st.markdown('---')
    s=stats(); p=user_profile(u)
    a,b,c,d=st.columns(4)
    a.metric('ผู้ใช้ทั้งหมด',s['users']); b.metric('มอเตอร์ไซค์',s['motorcycles']); c.metric('ความสัมพันธ์ LIKES',s['likes']); d.metric('คะแนนเฉลี่ย',f"{float(s['avg_rating']):.2f}/5")
    st.divider()
    left,right=st.columns([1,2])
    with left:
        st.markdown(f'<div class="section">โปรไฟล์ · {u}</div>',unsafe_allow_html=True)
        st.metric('รถที่ชอบ',p['likes']); st.metric('คะแนนเฉลี่ยที่ให้',f"{float(p['avg_rating']):.2f}/5")
        st.caption('เลือกชื่อผู้ใช้ด้านบนเพื่อดูข้อมูลของแต่ละคน')
    with right:
        st.markdown('<div class="section">ความชอบล่าสุด</div>',unsafe_allow_html=True)
        h=history(u)
        if h: dataframe(h,{'motorcycle':'มอเตอร์ไซค์','rating':'คะแนน','date':'วันที่'})
        else: st.info('ผู้ใช้นี้ยังไม่มีข้อมูลความชอบ')
    st.markdown('<div class="section">มอเตอร์ไซค์ยอดนิยมในระบบ</div>',unsafe_allow_html=True)
    motorcycle_cards(popular(6))

elif page=='แนะนำสำหรับคุณ':
    u=user_picker('recommend_user')
    st.caption('เลือกผู้ใช้ → ระบบหา User ที่ชอบรถเหมือนกัน → นำรถที่คนเหล่านั้นชอบ แต่ผู้ใช้นี้ยังไม่เคยเลือก มาคำนวณและจัดอันดับ')
    n=st.slider('จำนวนคำแนะนำ',3,10,6)
    result=recommend(u,n)
    st.markdown(f'<div class="section">✨ แนะนำสำหรับ {u}</div>',unsafe_allow_html=True)
    motorcycle_cards(result,True)
    if not result: st.info('ข้อมูลความสัมพันธ์ของผู้ใช้นี้ยังไม่พอสำหรับสร้างคำแนะนำ ลองเพิ่มความชอบในเมนู “บันทึกความชอบ”')

elif page=='บันทึกความชอบ':
    u=user_picker('pref_user')
    rows=catalog(); names=[x['name'] for x in rows]
    m=st.selectbox('เลือกมอเตอร์ไซค์',names)
    row=next(x for x in rows if x['name']==m)
    left,right=st.columns([1,1.5])
    with left: show_image(row)
    with right:
        st.subheader(m); st.caption('บันทึกว่าผู้ใช้สนใจ/ชอบรถรุ่นนี้ เพื่อใช้สร้างความสัมพันธ์ใน Neo4j')
        with st.form('preference_form'):
            rating=st.slider('คะแนนความชอบ',1.0,5.0,4.0,.5)
            d=st.date_input('วันที่บันทึก',date.today(),max_value=date.today())
            submitted=st.form_submit_button('บันทึกความชอบ',type='primary',use_container_width=True)
        if submitted:
            save_preference(u,m,rating,d.isoformat()); st.success('บันทึก LIKES และคะแนนเรียบร้อย'); st.rerun()
    mine=liked(u)
    if mine:
        st.divider(); st.subheader(f'รายการที่ {u} ชอบอยู่')
        remove=st.selectbox('เลือกรายการหากต้องการลบความชอบ',[x['name'] for x in mine])
        if st.button('ลบความชอบที่เลือก'):
            remove_preference(u,remove); st.success('ลบแล้ว'); st.rerun()

elif page=='ประวัติความชอบ':
    u=user_picker('history_user')
    h=history(u)
    st.markdown(f'<div class="section">ประวัติของ {u}</div>',unsafe_allow_html=True)
    if h:
        df=pd.DataFrame(h).rename(columns={'motorcycle':'มอเตอร์ไซค์','rating':'คะแนน','date':'วันที่'})
        c1,c2,c3=st.columns(3); c1.metric('จำนวนรถที่ชอบ',len(df)); c2.metric('คะแนนเฉลี่ย',f"{df['คะแนน'].mean():.2f}/5"); c3.metric('คะแนนสูงสุด',f"{df['คะแนน'].max():.1f}/5")
        st.dataframe(df,hide_index=True,use_container_width=True)
        st.bar_chart(df.set_index('มอเตอร์ไซค์')['คะแนน'],horizontal=True)
    else: st.info('ยังไม่มีประวัติความชอบ')

elif page=='กราฟความสัมพันธ์':
    mode=st.radio('แสดงกราฟ',['เฉพาะผู้ใช้ที่เลือก','ผู้ใช้ทั้งหมด'],horizontal=True)
    u=user_picker('graph_user') if mode=='เฉพาะผู้ใช้ที่เลือก' else None
    edges=graph_edges(u)
    dot=['digraph G {','rankdir=LR;','graph [bgcolor="transparent", pad="0.3"];','node [fontname="Arial", margin="0.15"];','edge [fontname="Arial", color="#9CA3AF"];']
    for e in edges:
        uid='u:'+e['user']; mid='m:'+e['motorcycle']
        dot += [f'{json.dumps(uid)} [label={json.dumps(e["user"])} shape=ellipse style=filled fillcolor="#DBEAFE" color="#93C5FD"];',
                f'{json.dumps(mid)} [label={json.dumps(e["motorcycle"])} shape=box style="rounded,filled" fillcolor="#F3F4F6" color="#D1D5DB"];',
                f'{json.dumps(uid)} -> {json.dumps(mid)} [label={json.dumps("LIKES · "+str(e["rating"] if e["rating"] is not None else "-"))}];']
    st.graphviz_chart('\n'.join(dot+['}']),use_container_width=True)
    if edges: dataframe(edges,{'user':'ผู้ใช้','motorcycle':'มอเตอร์ไซค์','rating':'คะแนน','date':'วันที่'})
    else: st.info('ยังไม่มีความสัมพันธ์')

elif page=='จัดการข้อมูล':
    tab1,tab2,tab3=st.tabs(['🏍️ มอเตอร์ไซค์','👤 ผู้ใช้','🖼️ รูปภาพ'])
    with tab1:
        st.subheader('เพิ่มมอเตอร์ไซค์ใหม่')
        with st.form('add_motorcycle_form'):
            name=st.text_input('ชื่อมอเตอร์ไซค์')
            upload=st.file_uploader('รูปรถ',type=['jpg','jpeg','png','webp'])
            url=st.text_input('หรือ URL รูปภาพ (https://)')
            add=st.form_submit_button('เพิ่มมอเตอร์ไซค์',type='primary')
        if add:
            try:
                data=''
                if upload:
                    im=Image.open(upload).convert('RGB'); im.thumbnail((1200,900)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=88); data=base64.b64encode(buf.getvalue()).decode(); url=''
                if url and not (urlparse(url).scheme=='https' and urlparse(url).netloc): raise ValueError('URL ต้องขึ้นต้นด้วย https://')
                add_motorcycle(name,url.strip(),data); st.success('เพิ่มรถใหม่แล้ว'); st.rerun()
            except Exception as e: st.error(str(e))
        st.divider(); st.subheader('รายการมอเตอร์ไซค์ทั้งหมด')
        rows=catalog(); dataframe([{k:v for k,v in r.items() if k not in ('image_data','image_url')} for r in rows],{'name':'ชื่อรถ','avg_rating':'คะแนนเฉลี่ย','like_count':'จำนวนคนชอบ'})
        delete=st.selectbox('เลือกรถที่ต้องการลบ',[r['name'] for r in rows],key='delcar')
        if st.button('ลบมอเตอร์ไซค์',key='delete_car'):
            delete_motorcycle(delete); st.warning('ลบมอเตอร์ไซค์และความสัมพันธ์แล้ว'); st.rerun()
    with tab2:
        st.subheader('จัดการผู้ใช้')
        newuser=st.text_input('ชื่อผู้ใช้ใหม่')
        if st.button('เพิ่มผู้ใช้',type='primary'):
            try: add_user(newuser); st.success('เพิ่มผู้ใช้แล้ว'); st.rerun()
            except Exception as e: st.error(str(e))
        st.write('ผู้ใช้ในระบบ: '+', '.join(users()))
        delu=st.selectbox('เลือกผู้ใช้ที่ต้องการลบ',users(),key='deluser')
        if st.button('ลบผู้ใช้'):
            delete_user(delu); st.warning('ลบผู้ใช้และความสัมพันธ์แล้ว'); st.rerun()
    with tab3:
        st.subheader('แก้ไขรูปมอเตอร์ไซค์')
        rows=catalog(); m=st.selectbox('เลือกรถ',[x['name'] for x in rows],key='editcar'); row=next(x for x in rows if x['name']==m); show_image(row)
        upload=st.file_uploader('อัปโหลดรูปใหม่',type=['jpg','jpeg','png','webp'],key='editimg')
        url=st.text_input('หรือ URL ใหม่',value=row.get('image_url') or '',key='editurl')
        if st.button('บันทึกรูป',type='primary'):
            try:
                data=row.get('image_data') or ''
                if upload:
                    im=Image.open(upload).convert('RGB'); im.thumbnail((1200,900)); buf=io.BytesIO(); im.save(buf,'JPEG',quality=88); data=base64.b64encode(buf.getvalue()).decode(); url=''
                if url and not (urlparse(url).scheme=='https' and urlparse(url).netloc): raise ValueError('URL ต้องขึ้นต้นด้วย https://')
                save_image(m,url.strip(),data); st.success('บันทึกรูปแล้ว'); st.rerun()
            except Exception as e: st.error(str(e))
