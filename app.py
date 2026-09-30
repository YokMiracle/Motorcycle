from pathlib import Path
import base64
import io
import json
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import USERS, MODELS, catalog, liked, recommend, seed_demo_data, set_like, save_image, query

ROOT = Path(__file__).parent
st.set_page_config(page_title="Motorcycle Recommender", page_icon="🏍️", layout="wide")
st.title("🏍️ Motorcycle Recommendation System")
st.caption("ระบบแนะนำรถมอเตอร์ไซค์ด้วย Neo4j · 664245008")
page = st.sidebar.radio("เมนู", ["ภาพรวม", "รถที่แนะนำ", "ค้นหารถ", "บันทึกความชอบ", "กราฟความสัมพันธ์", "ตั้งค่า / รูปภาพ"])
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
                    st.write("ผู้ใช้ที่มีความชอบใกล้กัน: " + ", ".join(row["similar_users"]))
                    st.caption("ชอบรุ่นเดียวกัน: " + ", ".join(row["shared_models"]))

if page == "ตั้งค่า / รูปภาพ":
    st.subheader("สร้างข้อมูลจาก Notebook")
    st.caption("MERGE ข้อมูล 10 ผู้ใช้ 10 รุ่น และ 21 ความชอบ กดซ้ำได้ ไม่ลบข้อมูลเดิม และเก็บภาพที่เพิ่มไว้")
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
        st.info("ไปที่ ตั้งค่า / รูปภาพ แล้วกดสร้างข้อมูลตัวอย่าง")
        st.stop()
    user = st.sidebar.selectbox("ผู้ใช้", USERS)
    if page == "ภาพรวม":
        edges = query("MATCH (u:User)-[:LIKES]->(m:Motorcycle) WHERE u.name IN $users AND m.name IN $models RETURN u.name AS user, m.name AS motorcycle", {"users":USERS,"models":MODELS})
        a,b,c = st.columns(3)
        a.metric("ผู้ใช้ในชุดข้อมูล", len(USERS)); b.metric("รุ่นรถ", len(rows)); c.metric("ความชอบ", len(edges))
        st.subheader(f"รถที่ {user} ชอบ")
        cards(liked(user))
    elif page == "รถที่แนะนำ":
        top_n = st.slider("จำนวนคำแนะนำสูงสุด", 1, 10, 6)
        st.caption("คะแนน = จำนวนเส้นทาง ผู้ใช้ → รถที่ชอบ → ผู้ใช้อื่น → รถใหม่ · ตัดรุ่นที่ชอบแล้ว · คะแนนเท่ากันเรียงชื่อรุ่น")
        cards(recommend(user, top_n), True)
    elif page == "ค้นหารถ":
        keyword = st.text_input("ชื่อรุ่นหรือยี่ห้อ")
        cards([r for r in rows if keyword.lower() in r["name"].lower()])
    elif page == "บันทึกความชอบ":
        model = st.selectbox("รุ่นรถ", [r["name"] for r in rows])
        show_image(next(r for r in rows if r["name"] == model))
        enabled = st.radio("สถานะ", ["ชอบ", "ยกเลิกความชอบ"]) == "ชอบ"
        if st.button("บันทึก", type="primary"):
            set_like(user, model, enabled)
            st.success("บันทึกแล้ว ผลแนะนำจะคำนวณจากความชอบล่าสุด")
    elif page == "กราฟความสัมพันธ์":
        edges = query("MATCH (u:User)-[:LIKES]->(m:Motorcycle) WHERE u.name IN $users AND m.name IN $models RETURN u.name AS user, m.name AS motorcycle", {"users":USERS,"models":MODELS})
        dot = ["digraph G {", "rankdir=LR;"]
        for edge in edges:
            dot.append(f'{json.dumps("user:"+edge["user"])} [label={json.dumps(edge["user"])} shape=ellipse];')
            dot.append(f'{json.dumps("model:"+edge["motorcycle"])} [label={json.dumps(edge["motorcycle"])} shape=box];')
            dot.append(f'{json.dumps("user:"+edge["user"])} -> {json.dumps("model:"+edge["motorcycle"])} [label="LIKES"];')
        st.graphviz_chart("\n".join(dot+["}"]))
        st.dataframe(pd.DataFrame(edges), hide_index=True)
