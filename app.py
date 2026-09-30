from pathlib import Path
import base64,io,json
from PIL import Image
import streamlit as st
from neo4j_service import *
ROOT=Path(__file__).parent
st.set_page_config(page_title='Motorcycle Recommendation',page_icon='🏍️',layout='wide')
st.markdown('''<style>
.stApp{background:linear-gradient(120deg,#fff7f7,#f6f1ff)} .block-container{max-width:1280px;padding-top:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#25164b,#55207a);color:white}[data-testid="stSidebar"] *{color:white!important}
.hero{background:linear-gradient(110deg,#ef4388,#b64de8,#6469ff);padding:38px;border-radius:25px;color:white;box-shadow:0 18px 35px #d25edc33;margin-bottom:20px}.hero h1{font-size:2.3rem;margin:0 0 20px}.hero p{font-size:1.05rem;margin:0}
.stat{background:white;border-radius:20px;padding:22px;text-align:center;box-shadow:0 8px 25px #9b72bc16}.stat b{font-size:2.2rem;color:#a84be1}.stat span{display:block;color:#6e6879}.card{border:1px solid #ddd1df;border-radius:14px;padding:16px;margin-bottom:16px;background:#fff8fb}.pill{display:inline-block;background:#e8e9ff;color:#5360a9;padding:4px 12px;border-radius:20px;margin:3px}.stButton>button{border:0;border-radius:22px;background:linear-gradient(90deg,#ef4388,#b84de5);color:white;padding:.55rem 1.2rem}div[data-baseweb="select"]>div{background:#f3edff;border-color:#e65b98}</style>''',unsafe_allow_html=True)
with st.sidebar:
 st.markdown('### ผู้จัดทำ: ณัฏฐนันท์ เกียรติจิรยาดา')
 st.markdown('**รหัส: 664245008**'); st.write(''); st.write(''); st.markdown('**เมนู**')
 page=st.radio('', ['🔵 🏍️ แนะนำมอเตอร์ไซค์','🟣 👥 จัดการคน & เพื่อน','⚪ 🛵 จัดการรถ & การเลือก','⚪ 🕸️ กราฟความสัมพันธ์'],label_visibility='collapsed')
try: query('RETURN 1')
except Exception as e: st.error('เชื่อมต่อ Neo4j ไม่ได้'); st.code(str(e)); st.stop()
setup_data()
def hero(): st.markdown('<div class="hero"><h1>Motorcycle Recommendation</h1><p>แนะนำมอเตอร์ไซค์จากเพื่อนของคุณ ด้วย Neo4j Graph Database</p></div>',unsafe_allow_html=True)
def summary():
 s=stats(); cols=st.columns(4); vals=[(s['users'],'👤 คน'),(s['motorcycles'],'🏍️ มอเตอร์ไซค์'),(s['friendships'],'🤝 ความเป็นเพื่อน'),(s['orders'],'📋 การเลือก')]
 for c,(v,l) in zip(cols,vals): c.markdown(f'<div class="stat"><b>{v}</b><span>{l}</span></div>',unsafe_allow_html=True)
def img(r):
 try:
  if r.get('image_data'): st.image(base64.b64decode(r['image_data']),use_container_width=True)
  elif r.get('image_url'): st.image(r['image_url'],use_container_width=True)
 except: pass
hero(); summary(); st.write('')
U=users()
if page.startswith('🔵'):
 u=st.selectbox('เลือกชื่อของคุณ',U); fs=friends(u); st.markdown('เพื่อนของ '+u+': '+' '.join(f'<span class="pill">{x}</span>' for x in fs),unsafe_allow_html=True)
 rec=recommendations(u); st.markdown(f'## ✨ มอเตอร์ไซค์แนะนำสำหรับ {u} ({len(rec)})')
 if not rec: st.info('ยังไม่มีคำแนะนำใหม่ ลองเพิ่มเพื่อนหรือเพิ่มข้อมูลการเลือกมอเตอร์ไซค์')
 cols=st.columns(3)
 for i,r in enumerate(rec):
  with cols[i%3]:
   st.markdown('<div class="card">',unsafe_allow_html=True); img(r); st.subheader(r['name']); st.markdown('เพื่อนที่เลือก: '+' '.join(f'<span class="pill">{x}</span>' for x in r['friend_names']),unsafe_allow_html=True)
   if st.button('🏍️ ฉันเลือกรุ่นนี้แล้ว',key='rec'+r['name']): order(u,r['name']); st.rerun()
   st.markdown('</div>',unsafe_allow_html=True)
elif page.startswith('🟣'):
 t1,t2,t3=st.tabs(['➕ เพิ่มคน','🤝 เพิ่มความสัมพันธ์','✂️ ลบ'])
 with t1:
  n=st.text_input('ชื่อคนใหม่');
  if st.button('➕ เพิ่มคน') and n: add_user(n); st.rerun()
 with t2:
  c1,c2=st.columns(2); a=c1.selectbox('คนที่ 1',U); b=c2.selectbox('คนที่ 2',U,index=min(1,len(U)-1)); st.markdown('เพื่อนของ '+a+' ตอนนี้: '+' '.join(f'<span class="pill">{x}</span>' for x in friends(a)),unsafe_allow_html=True)
  if st.button('🤝 เชื่อมเป็นเพื่อนกัน'): add_friend(a,b); st.rerun()
 with t3:
  st.subheader('ลบความสัมพันธ์'); a=st.selectbox('เลือกคน',U,key='rf'); f=friends(a)
  if f:
   b=st.selectbox('เลือกเพื่อนที่จะลบ',f); 
   if st.button('ลบความสัมพันธ์'): remove_friend(a,b); st.rerun()
  st.divider(); st.subheader('ลบคน (ความสัมพันธ์และการเลือกของคนนั้นจะหายด้วย)'); d=st.selectbox('เลือกคนที่จะลบ',U,key='du'); ok=st.checkbox('ยืนยันลบ '+d)
  if st.button('ลบคน') and ok: delete_user(d); st.rerun()
elif page.startswith('⚪ 🛵'):
 t1,t2,t3=st.tabs(['➕ เพิ่มมอเตอร์ไซค์','📋 บันทึกการเลือก','🗑️ ลบมอเตอร์ไซค์'])
 with t1:
  n=st.text_input('ชื่อมอเตอร์ไซค์'); price=st.number_input('ราคา (บาท)',0,10000000,0,1000); up=st.file_uploader('รูปภาพ (ไม่บังคับ)',type=['jpg','jpeg','png','webp'])
  if st.button('เพิ่มมอเตอร์ไซค์'):
   data=''
   if up:
    im=Image.open(up).convert('RGB'); im.thumbnail((1200,900)); b=io.BytesIO(); im.save(b,'JPEG',quality=88); data=base64.b64encode(b.getvalue()).decode()
   add_motorcycle(n,price,data=data); st.rerun()
 with t2:
  u=st.selectbox('ใครเลือก?',U); M=[x['name'] for x in motorcycles()]; choices=st.multiselect('เลือกมอเตอร์ไซค์อะไร?',M)
  if st.button('📋 บันทึกการเลือก'):
   for m in choices: order(u,m)
   st.rerun()
  old=ordered(u); st.markdown('**'+u+' เคยเลือก:**');
  for x in old:
   c1,c2=st.columns([8,1]); c1.markdown(f'<span class="pill">{x["name"]}</span>',unsafe_allow_html=True)
   if c2.button('ลบ',key='o'+x['name']): remove_order(u,x['name']); st.rerun()
 with t3:
  M=[x['name'] for x in motorcycles()]; d=st.selectbox('เลือกรถที่จะลบ',M)
  if st.button('ลบมอเตอร์ไซค์'): delete_motorcycle(d); st.rerun()
else:
 c1,c2=st.columns([2,1]); who=c1.selectbox('ไฮไลต์คน',['— ทุกคน —']+U); show=c2.checkbox('แสดงมอเตอร์ไซค์ที่เลือก',True)
 fs,os=edges(None if who=='— ทุกคน —' else who,show); dot=['graph G {','layout=neato; overlap=false; splines=true; bgcolor="transparent";','node [fontname="Arial"];']
 hi=None if who=='— ทุกคน —' else who
 people=set([x['a'] for x in fs]+[x['b'] for x in fs]+[x['a'] for x in os])
 bikes=set(x['b'] for x in os)
 for p in people:
  color='#ef3b83' if p==hi else '#dcd9ff'; dot.append(f'{json.dumps("u"+p)} [label={json.dumps(p)},shape=circle,style=filled,fillcolor="{color}",color="white",width=1];')
 for m in bikes: dot.append(f'{json.dumps("m"+m)} [label={json.dumps(m)},shape=box,style="rounded,filled",fillcolor="#ffe0a8",color="white"];')
 seen=set()
 for e in fs:
  k=tuple(sorted((e['a'],e['b'])));
  if k not in seen: dot.append(f'{json.dumps("u"+e["a"])} -- {json.dumps("u"+e["b"])} [color="#9db7ff",penwidth=2];'); seen.add(k)
 for e in os: dot.append(f'{json.dumps("u"+e["a"])} -- {json.dumps("m"+e["b"])} [color="#d9b66c",style=dashed];')
 dot.append('}'); st.graphviz_chart('\n'.join(dot),use_container_width=True)
