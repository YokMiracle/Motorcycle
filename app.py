from pathlib import Path
import base64, io, json
from datetime import date
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import (USERS, catalog, liked, recommend, seed_demo_data, rental_history,
    record_rental, save_image, add_motorcycle, query)

ROOT = Path(__file__).parent
st.set_page_config(page_title="Motorcycle Graph Recommendation", page_icon="🏍️", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1400px}.hero{padding:1.6rem 1.8rem;border-radius:20px;background:linear-gradient(125deg,#172033,#24324a 55%,#385b70);color:#fff;margin-bottom:1.1rem;box-shadow:0 8px 24px #00000014}.hero h1{margin:0;color:#fff;font-size:2rem}.hero p{margin:.4rem 0 0;opacity:.88}.section-note{color:#667085;font-size:.92rem}[data-testid="stSidebar"]{background:#f7f8fa}.stMetric{background:#fff;border:1px solid #e6e8ec;padding:14px;border-radius:16px}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.image(str(ROOT/"img.jpg"), width=140)
    st.markdown("## 🏍️ GraphMotorcycle")
    st.caption("Motorcycle Rental Recommendation")
    page=st.radio("เมนู",["ภาพรวมระบบ","รถแนะนำสำหรับคุณ","ค้นหารถเช่า","ประวัติการเช่า / ให้คะแนน","กราฟการเช่ารถ","จัดการข้อมูล / รูปภาพ"])
    st.divider()
    st.caption("Neo4j Graph Database + Streamlit")

st.markdown('<div class="hero"><h1>🏍️ Motorcycle Graph Recommendation</h1><p>ระบบแนะนำรถมอเตอร์ไซค์จากความสัมพันธ์ ประวัติการเช่า และคะแนนของผู้ใช้</p></div>',unsafe_allow_html=True)
try: query("RETURN 1 AS ok")
except Exception:
    st.error("ยังเชื่อมต่อ Neo4j ไม่ได้ กรุณาตั้งค่า .streamlit/secrets.toml ตาม README"); st.stop()

def image_bytes(upload):
    if upload.size>5*1024*1024: raise ValueError("ภาพต้องไม่เกิน 5 MB")
    im=Image.open(upload).convert("RGB"); im.thumbnail((1200,900)); buf=io.BytesIO(); im.save(buf,format="JPEG",quality=88)
    return base64.b64encode(buf.getvalue()).decode()

def show_image(row):
    try:
        if row.get("image_data"): st.image(base64.b64decode(row["image_data"]),use_container_width=True)
        elif row.get("image_url"): st.image(row["image_url"],use_container_width=True)
        else: st.image(str(ROOT/"assets"/"placeholder.png"),use_container_width=True)
    except Exception: st.image(str(ROOT/"assets"/"placeholder.png"),use_container_width=True)

def cards(rows,recommendations=False):
    if not rows: st.info("ไม่มีรายการสำหรับเงื่อนไขนี้"); return
    cols=st.columns(3)
    for i,row in enumerate(rows):
        with cols[i%3]:
            with st.container(border=True):
                show_image(row); st.subheader(row["name"])
                if recommendations:
                    st.write(f"อันดับ {i+1} · คะแนนแนะนำ {row['score']:.2f}")
                    st.caption(f"⭐ {row['avg_rating']:.2f}/5 · {row['rating_count']} รีวิว")
                    if row.get("similar_users"): st.write("ผู้ใช้ที่มีความสัมพันธ์ใกล้เคียง: "+", ".join(row["similar_users"]))

rows=catalog()

if page=="จัดการข้อมูล / รูปภาพ":
    st.subheader("⚙️ จัดการข้อมูล")
    tab1,tab2=st.tabs(["➕ เพิ่มรถใหม่","🖼️ แก้ไขรูปรถ"])
    with tab1:
        st.write("เพิ่มรถมอเตอร์ไซค์ใหม่เข้าสู่ Neo4j และให้รถรุ่นนี้ใช้งานต่อในระบบได้")
        with st.form("add_motorcycle_form",clear_on_submit=True):
            name=st.text_input("ชื่อรถ / รุ่นรถ",placeholder="เช่น Honda PCX 160")
            upload=st.file_uploader("รูปรถ JPG / PNG / WebP",type=["jpg","jpeg","png","webp"],key="new_img")
            url=st.text_input("หรือ URL รูปภาพ (https://)",key="new_url")
            submitted=st.form_submit_button("เพิ่มรถใหม่",type="primary")
        if submitted:
            try:
                data=image_bytes(upload) if upload else ""
                clean_url=url.strip() if urlparse(url.strip()).scheme=="https" else ""
                if not upload and url.strip() and not clean_url: raise ValueError("URL รูปภาพต้องเป็น https://")
                add_motorcycle(name,clean_url,data); st.success(f"เพิ่ม {name.strip()} แล้ว"); st.rerun()
            except Exception as e: st.error(str(e))
        st.divider(); st.markdown("#### รถทั้งหมดในระบบ")
        st.dataframe(pd.DataFrame([{"ชื่อรถ":r["name"],"มีรูป":bool(r.get("image_data") or r.get("image_url"))} for r in catalog()]),hide_index=True,use_container_width=True)
    with tab2:
        current=catalog()
        if not current: st.info("ยังไม่มีข้อมูลรถ")
        else:
            model=st.selectbox("เลือกรถที่ต้องการแก้ไข",[r["name"] for r in current])
            row=next(r for r in current if r["name"]==model); c1,c2=st.columns([1,2])
            with c1: show_image(row)
            with c2:
                upload=st.file_uploader("อัปโหลดรูปใหม่",type=["jpg","jpeg","png","webp"],key="edit_img")
                url=st.text_input("หรือ URL รูปภาพ",value=row.get("image_url") or "",key="edit_url")
                if st.button("บันทึกรูป",type="primary"):
                    try:
                        if upload: save_image(model,image_data=image_bytes(upload))
                        elif urlparse(url).scheme=="https" and urlparse(url).netloc: save_image(model,url=url.strip())
                        else: raise ValueError("เลือกไฟล์ภาพหรือใส่ URL https ที่ถูกต้อง")
                        st.success("บันทึกรูปแล้ว"); st.rerun()
                    except Exception as e: st.error(str(e))
    st.divider()
    with st.expander("สร้างข้อมูลตัวอย่างเริ่มต้น"):
        st.caption("ใช้สำหรับสร้างผู้ใช้/รถ/ความสัมพันธ์ตัวอย่างเดิม โดยไม่ลบข้อมูลที่เพิ่มภายหลัง")
        if st.button("สร้างข้อมูลตัวอย่าง"): seed_demo_data(); st.success("สร้างข้อมูลตัวอย่างแล้ว"); st.rerun()
else:
    if not rows:
        st.warning("ยังไม่มีข้อมูลรถ ไปที่หน้าจัดการข้อมูลเพื่อสร้างข้อมูลตัวอย่างก่อน"); st.stop()

    # Each analytical page has its own user selector, matching the reference workflow.
    if page=="ภาพรวมระบบ":
        edges=query("MATCH (u:User)-[r:RENTED]->(m:Motorcycle) WHERE u.name IN $users RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating",{"users":USERS})
        a,b,c,d=st.columns(4); a.metric("ผู้ใช้",len(USERS)); b.metric("รุ่นรถ",len(rows)); c.metric("รายการเช่า",len(edges)); d.metric("คะแนนเฉลี่ย / 5",f"{sum((e['rating'] or 0) for e in edges)/max(sum(e['rating'] is not None for e in edges),1):.2f}")
        st.divider()
        user=st.selectbox("เลือกชื่อผู้ใช้เพื่อดูภาพรวม",USERS,key="overview_user")
        history=rental_history(user); left,right=st.columns([1,2])
        with left: st.subheader(f"👤 {user}"); st.write("**จำนวนครั้งที่เช่า:**",len(history)); st.write("**รุ่นที่เคยเช่า:**",len({h['name'] for h in history}))
        with right: st.subheader("ประวัติการเช่า"); st.dataframe(pd.DataFrame(history),hide_index=True,use_container_width=True)
        st.subheader("รถที่เคยเช่า"); cards(liked(user))
    elif page=="รถแนะนำสำหรับคุณ":
        st.subheader("✨ รถแนะนำสำหรับคุณ")
        user=st.selectbox("เลือกชื่อผู้ใช้",USERS,key="rec_user"); top_n=st.slider("จำนวนคำแนะนำ",1,10,6)
        st.caption("แนะนำจากผู้ใช้ที่เคยเช่ารถรุ่นเดียวกัน และตัดรถที่ผู้ใช้นี้เคยเช่าแล้ว")
        cards(recommend(user,top_n),True)
    elif page=="ค้นหารถเช่า":
        st.subheader("🔎 ค้นหารถเช่า"); keyword=st.text_input("ค้นหาชื่อหรือรุ่นรถ",placeholder="พิมพ์ชื่อรถ...")
        cards([r for r in rows if keyword.lower() in r['name'].lower()])
    elif page=="ประวัติการเช่า / ให้คะแนน":
        st.subheader("📝 ประวัติการเช่า / ให้คะแนน")
        user=st.selectbox("เลือกชื่อผู้ใช้",USERS,key="history_user")
        model=st.selectbox("เลือกรุ่นรถ",[r['name'] for r in rows]); show_image(next(r for r in rows if r['name']==model))
        with st.form("rental_form",clear_on_submit=True):
            rental_date=st.date_input("วันที่เช่า",value=date.today(),max_value=date.today()); rating=st.slider("คะแนนความพึงพอใจ",1.0,5.0,4.0,.5); submit=st.form_submit_button("บันทึก",type="primary")
        if submit:
            try: record_rental(user,model,rental_date.isoformat(),rating); st.success("บันทึกประวัติและคะแนนแล้ว"); st.rerun()
            except ValueError as e: st.error(str(e))
        st.dataframe(pd.DataFrame(rental_history(user)),hide_index=True,use_container_width=True)
    elif page=="กราฟการเช่ารถ":
        st.subheader("🕸️ กราฟความสัมพันธ์การเช่ารถ")
        user=st.selectbox("เลือกชื่อผู้ใช้",["ผู้ใช้ทั้งหมด"]+USERS,key="graph_user")
        if user=="ผู้ใช้ทั้งหมด": edges=query("MATCH (u:User)-[r:RENTED]->(m:Motorcycle) WHERE u.name IN $users RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating",{"users":USERS})
        else: edges=query("MATCH (u:User {name:$user})-[r:RENTED]->(m:Motorcycle) RETURN u.name AS user,m.name AS motorcycle,r.rating AS rating",{"user":user})
        dot=["digraph G {","rankdir=LR;","node [fontname=\"Arial\"];"]
        for e in edges:
            dot += [f'{json.dumps("user:"+e["user"])} [label={json.dumps(e["user"])} shape=ellipse];',f'{json.dumps("model:"+e["motorcycle"])} [label={json.dumps(e["motorcycle"])} shape=box];',f'{json.dumps("user:"+e["user"])} -> {json.dumps("model:"+e["motorcycle"])} [label="RENTED / {e["rating"] if e["rating"] is not None else "-"}"];']
        st.graphviz_chart("\n".join(dot+["}"]),use_container_width=True); st.dataframe(pd.DataFrame(edges),hide_index=True,use_container_width=True)
