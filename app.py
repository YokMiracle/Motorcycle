from pathlib import Path
import base64
import io
import json
from datetime import date, timedelta
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import USERS, MODELS, catalog, liked, recommend, seed_demo_data, rental_history, record_rental, return_rental, save_image, query

ROOT = Path(__file__).parent
st.set_page_config(page_title="Motorcycle Recommender", page_icon="🏍️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top:1.3rem;padding-bottom:2rem;}
.hero {padding:1.4rem 1.6rem;border-radius:22px;background:linear-gradient(120deg,#111827 0%,#1f2937 55%,#0f766e 100%);color:white;margin-bottom:1rem;}
.hero h1 {margin:0;font-size:2.15rem;color:white;}
.hero p {opacity:.88;margin:.35rem 0 0 0;}
[data-testid="stSidebar"] {background:#f0f2f6;}
</style>
""", unsafe_allow_html=True)
with st.sidebar:
    st.image(str(ROOT / "img.jpg"), width=150)
    st.markdown("## 🏍️ GraphMotorcycle")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio("เมนู", ["ภาพรวมระบบ", "รถแนะนำสำหรับคุณ", "ค้นหารถเช่า", "เช่ารถ / ให้คะแนน", "กราฟการเช่ารถ", "จัดการข้อมูล / รูปภาพ"])
    st.divider()
    st.caption("Bachelor-level Graph Database Project")
st.markdown("""
<div class="hero"><h1>🏍️ GraphMotorcycle Rental & Recommendation</h1>
<p>ระบบเช่าและแนะนำรถมอเตอร์ไซค์จากประวัติการเช่าด้วย Graph Database</p></div>
""", unsafe_allow_html=True)

try:
    query("RETURN 1 AS ok")
except Exception:
    st.error("ยังเชื่อมต่อ Neo4j ไม่ได้ กรุณาตั้งค่า .streamlit/secrets.toml ตาม README")
    st.stop()

def show_image(row):
    try:
        if row.get("image_data"):
            st.image(base64.b64decode(row["image_data"]), use_container_width=True)
        elif row.get("image_url"):
            st.image(row["image_url"], use_container_width=True)
            st.caption("ภาพจาก URL ที่ตั้งค่าไว้ หากไม่โหลดให้อัปโหลดภาพแทน")
        else:
            bundled = next((m.get("image_data") for m in __import__("neo4j_service").DATA["motorcycles"] if m["name"] == row["name"]), None)
            if bundled:
                st.image(base64.b64decode(bundled), use_container_width=True)
                return
            st.image(str(ROOT / "assets" / "placeholder.png"), use_container_width=True)
            st.caption("ภาพตัวอย่าง — ยังไม่ได้เพิ่มภาพจริงของรุ่นนี้")
    except Exception:
        st.image(str(ROOT / "assets" / "placeholder.png"), use_container_width=True)
        st.caption("โหลดภาพไม่ได้ กรุณาแก้ภาพในหน้าตั้งค่า")

def cards(rows, recommendations=False):
    if not rows:
        st.info("ไม่มีรายการสำหรับเงื่อนไขนี้")
    columns = st.columns(3)
    for i, row in enumerate(rows):
        with columns[i % 3]:
            with st.container(border=True):
                show_image(row)
                st.subheader(row["name"])
                if recommendations:
                    st.write(f"อันดับ {i+1} · คะแนน {row['score']}")
                    st.write("ผู้ใช้ที่เคยเช่ารถรุ่นเดียวกัน: " + ", ".join(row["similar_users"]))
                    st.caption("เคยเช่ารุ่นเดียวกัน: " + ", ".join(row["shared_models"]))

if page == "จัดการข้อมูล / รูปภาพ":
    st.subheader("สร้างข้อมูลจาก Notebook")
    st.caption("ข้อมูล 10 ผู้ใช้ 10 รุ่น และประวัติเช่าจำลอง 21 รายการจากคู่ความชอบต้นทาง วันที่และสถานะเป็นตัวอย่าง กดซ้ำไม่เพิ่มประวัติเช่าจำลองซ้ำ")
    if st.button("สร้างข้อมูลตัวอย่าง", type="primary"):
        seed_demo_data()
        st.success("เพิ่มข้อมูลแล้ว")
    st.subheader("เพิ่มภาพรถแต่ละรุ่น")
    rows = catalog()
    if not rows:
        st.info("กดสร้างข้อมูลตัวอย่างก่อน")
    else:
        model = st.selectbox("รุ่นรถ", [r["name"] for r in rows])
        row = next(r for r in rows if r["name"] == model)
        show_image(row)
        upload = st.file_uploader("อัปโหลดภาพจริง JPG / PNG / WebP (ไม่เกิน 5 MB)", type=["jpg", "jpeg", "png", "webp"])
        url = st.text_input("หรือ URL รูปภาพโดยตรง (https://)", value=row.get("image_url") or "")
        st.caption("ภาพอัปโหลดเก็บใน Neo4j จึงยังแสดงได้หลังรีสตาร์ตหรือย้ายเครื่อง")
        if st.button("บันทึกภาพ"):
            if upload:
                try:
                    if upload.size > 5*1024*1024:
                        raise ValueError("ภาพต้องไม่เกิน 5 MB")
                    im = Image.open(upload).convert("RGB")
                    im.thumbnail((1200, 900))
                    buf = io.BytesIO(); im.save(buf, format="JPEG", quality=88)
                    save_image(model, image_data=base64.b64encode(buf.getvalue()).decode())
                    st.rerun()
                except Exception as exc:
                    st.error(f"บันทึกภาพไม่สำเร็จ: {exc}")
            elif urlparse(url).scheme == "https" and urlparse(url).netloc:
                save_image(model, url=url.strip()); st.rerun()
            else:
                st.error("เลือกไฟล์ภาพหรือใส่ URL https ที่ถูกต้อง")
else:
    rows = catalog()
    if not rows:
        st.info("ไปที่ จัดการข้อมูล / รูปภาพ แล้วกดสร้างข้อมูลตัวอย่าง")
        st.stop()
    user = st.selectbox("เลือกผู้ใช้", USERS)
    if page == "ภาพรวมระบบ":
        edges = query("MATCH (u:User)-[:RENTED]->(m:Motorcycle) WHERE u.name IN $users AND m.name IN $models RETURN u.name AS user, m.name AS motorcycle", {"users":USERS,"models":MODELS})
        a,b,c,d = st.columns(4)
        a.metric("ผู้ใช้", len(USERS)); b.metric("รุ่นรถเช่า", len(rows)); c.metric("รายการเช่าทั้งหมด", len(edges))
        all_status = query("MATCH (u:User)-[r:RENTED]->(m:Motorcycle) WHERE u.name IN $users AND m.name IN $models AND r.status='active' RETURN count(r) AS n", {"users":USERS,"models":MODELS})
        d.metric("รายการที่ยังไม่คืนรถ", all_status[0]["n"])
        st.divider()
        left,right = st.columns([1,2])
        history = rental_history(user)
        with left:
            st.subheader(user)
            st.write("**จำนวนครั้งที่เช่า:**", len(history))
            st.write("**รุ่นที่เคยเช่า:**", len({h["name"] for h in history}))
        with right:
            st.subheader("ประวัติการเช่ารถ")
            st.caption("is_demo = True หมายถึงประวัติจำลองสำหรับสาธิต")
            st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)
        st.subheader("รถที่เคยเช่า")
        cards(liked(user))
    elif page == "รถแนะนำสำหรับคุณ":
        st.subheader("✨ รถมอเตอร์ไซค์ที่แนะนำ")
        top_n = st.slider("จำนวนคำแนะนำสูงสุด", 1, 10, 6)
        st.caption("คะแนน = จำนวนเส้นทาง ผู้ใช้ → รถที่เคยเช่า → ผู้ใช้อื่น → รถรุ่นใหม่ · ตัดรุ่นที่เคยเช่าแล้ว · การเช่ารุ่นเดิมซ้ำไม่เพิ่มคะแนนซ้ำ")
        cards(recommend(user, top_n), True)
    elif page == "ค้นหารถเช่า":
        st.subheader("🔎 ค้นหารถมอเตอร์ไซค์")
        keyword = st.text_input("ชื่อรุ่นหรือยี่ห้อ")
        cards([r for r in rows if keyword.lower() in r["name"].lower()])
    elif page == "เช่ารถ / ให้คะแนน":
        st.subheader("📝 บันทึกการเช่ารถ")
        model = st.selectbox("รุ่นรถ", [r["name"] for r in rows])
        show_image(next(r for r in rows if r["name"] == model))
        with st.form("rental_form"):
            start = st.date_input("วันเริ่มเช่า", value=date.today())
            end = st.date_input("วันกำหนดคืนรถ", value=date.today()+timedelta(days=1))
            submit = st.form_submit_button("บันทึกการเช่า", type="primary")
        if submit:
            try:
                record_rental(user, model, start.isoformat(), end.isoformat())
                st.success("บันทึกการเช่าแล้ว")
            except ValueError as exc:
                st.error(str(exc))
        st.divider()
        st.subheader("คืนรถ / ให้คะแนน")
        history = rental_history(user)
        if history:
            choices = {f"{h['name']} · {h['start_date']} · {h['rental_id']}":h["rental_id"] for h in history}
            with st.form("return_form"):
                selected = st.selectbox("รายการเช่า", list(choices))
                use_rating = st.checkbox("ให้คะแนนรถที่เช่า")
                rating = st.slider("คะแนน", 1.0, 5.0, 4.0, 0.5)
                done = st.form_submit_button("บันทึกคืนรถ / คะแนน")
            if done:
                return_rental(user, choices[selected], rating if use_rating else None)
                st.success("บันทึกคืนรถและคะแนนแล้ว")
        else:
            st.info("ยังไม่มีประวัติการเช่า")
    elif page == "กราฟการเช่ารถ":
        edges = query("MATCH (u:User)-[:RENTED]->(m:Motorcycle) WHERE u.name IN $users AND m.name IN $models RETURN u.name AS user, m.name AS motorcycle", {"users":USERS,"models":MODELS})
        dot = ["digraph G {", "rankdir=LR;"]
        for edge in edges:
            dot.append(f'{json.dumps("user:"+edge["user"])} [label={json.dumps(edge["user"])} shape=ellipse];')
            dot.append(f'{json.dumps("model:"+edge["motorcycle"])} [label={json.dumps(edge["motorcycle"])} shape=box];')
            dot.append(f'{json.dumps("user:"+edge["user"])} -> {json.dumps("model:"+edge["motorcycle"])} [label="RENTED"];')
        st.graphviz_chart("\n".join(dot+["}"]))
        st.dataframe(pd.DataFrame(edges), hide_index=True)
