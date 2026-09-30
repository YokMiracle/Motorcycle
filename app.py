from pathlib import Path
import base64
import io
import json
from datetime import date, timedelta
from urllib.parse import urlparse
import pandas as pd
from PIL import Image
import streamlit as st
from neo4j_service import USERS, MODELS, catalog, all_users, add_motorcycle, liked, recommend, seed_demo_data, rental_history, record_rental, save_image, query

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
    page = st.radio("เมนู", ["ภาพรวมระบบ", "รถแนะนำสำหรับคุณ", "ค้นหารถเช่า", "ประวัติการเช่า / ให้คะแนน", "กราฟการเช่ารถ", "จัดการข้อมูล / รูปภาพ"])
    st.divider()
    st.caption("Bachelor-level Graph Database Project")
st.markdown("""
<div class="hero"><h1>🏍️ GraphMotorcycle Rental Review & Recommendation</h1>
<p>ระบบแนะนำรถมอเตอร์ไซค์จากประวัติการเช่าและคะแนนของผู้ใช้</p></div>
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
                    st.write(f"อันดับ {i+1} · คะแนนแนะนำ {row['score']:.2f}")
                    st.write(f"⭐ คะแนนเฉลี่ย {row['avg_rating']:.2f}/5 จาก {row['rating_count']} รีวิว")
                    st.write("ผู้ใช้ที่เคยเช่ารถรุ่นเดียวกัน: " + ", ".join(row["similar_users"]))
                    st.caption("เคยเช่ารุ่นเดียวกัน: " + ", ".join(row["shared_models"]))

if page == "จัดการข้อมูล / รูปภาพ":
    st.subheader("➕ เพิ่มรถมอเตอร์ไซค์ใหม่")
    st.caption("เพิ่มรถใหม่เข้าฐานข้อมูล Neo4j พร้อมชื่อรถและรูปภาพ รถที่เพิ่มจะนำไปใช้ในหน้าค้นหาและบันทึกประวัติการเช่าได้ทันที")
    with st.form("add_motorcycle_form", clear_on_submit=True):
        new_name = st.text_input("ชื่อรถ / รุ่นรถ", placeholder="เช่น Honda PCX 160")
        new_upload = st.file_uploader("รูปรถ JPG / PNG / WebP (ไม่เกิน 5 MB)", type=["jpg", "jpeg", "png", "webp"], key="new_motorcycle_image")
        new_url = st.text_input("หรือ URL รูปรถ (https://)", placeholder="https://...")
        add_submit = st.form_submit_button("เพิ่มรถใหม่", type="primary")
    if add_submit:
        try:
            image_data = ""
            image_url = ""
            if new_upload:
                if new_upload.size > 5*1024*1024:
                    raise ValueError("ภาพต้องไม่เกิน 5 MB")
                im = Image.open(new_upload).convert("RGB")
                im.thumbnail((1200, 900))
                buf = io.BytesIO(); im.save(buf, format="JPEG", quality=88)
                image_data = base64.b64encode(buf.getvalue()).decode()
            elif new_url.strip():
                parsed = urlparse(new_url.strip())
                if parsed.scheme != "https" or not parsed.netloc:
                    raise ValueError("URL รูปต้องเป็น https:// ที่ถูกต้อง")
                image_url = new_url.strip()
            else:
                raise ValueError("กรุณาเลือกรูปรถหรือใส่ URL รูป")
            add_motorcycle(new_name, url=image_url, image_data=image_data)
            st.success(f"เพิ่ม {new_name.strip()} เรียบร้อยแล้ว")
            st.rerun()
        except Exception as exc:
            st.error(f"เพิ่มรถไม่สำเร็จ: {exc}")

    st.divider()
    st.subheader("สร้างข้อมูลจาก Notebook")
    st.caption("ข้อมูล 10 ผู้ใช้ 10 รุ่น และประวัติเคยเช่าและคะแนนจำลอง 21 รายการจากคู่ความชอบต้นทาง วันที่และคะแนนเป็นตัวอย่าง กดซ้ำไม่เพิ่มประวัติเช่าจำลองซ้ำ")
    if st.button("สร้างข้อมูลตัวอย่าง"):
        seed_demo_data()
        st.success("เพิ่มข้อมูลแล้ว")
    st.subheader("แก้ไขภาพรถแต่ละรุ่น")
    rows = catalog()
    if not rows:
        st.info("ยังไม่มีข้อมูลรถ กรุณาเพิ่มรถใหม่หรือสร้างข้อมูลตัวอย่าง")
    else:
        model = st.selectbox("รุ่นรถ", [r["name"] for r in rows])
        row = next(r for r in rows if r["name"] == model)
        show_image(row)
        upload = st.file_uploader("อัปโหลดภาพจริง JPG / PNG / WebP (ไม่เกิน 5 MB)", type=["jpg", "jpeg", "png", "webp"], key="edit_motorcycle_image")
        url = st.text_input("หรือ URL รูปภาพโดยตรง (https://)", value=row.get("image_url") or "", key="edit_motorcycle_url")
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
        st.info("ไปที่ จัดการข้อมูล / รูปภาพ แล้วเพิ่มรถหรือกดสร้างข้อมูลตัวอย่าง")
        st.stop()
    users = all_users() or USERS
    if page == "ภาพรวมระบบ":
        edges = query("MATCH (u:User)-[r:RENTED]->(m:Motorcycle) RETURN u.name AS user, m.name AS motorcycle, r.rating AS rating")
        a,b,c,d = st.columns(4)
        a.metric("ผู้ใช้", len(users)); b.metric("รุ่นรถเช่า", len(rows)); c.metric("รายการเช่าทั้งหมด", len(edges))
        rating_stats = query("MATCH (:User)-[r:RENTED]->(:Motorcycle) RETURN avg(r.rating) AS avg_rating")
        d.metric("คะแนนเฉลี่ย / 5", f"{(rating_stats[0]['avg_rating'] or 0):.2f}")
        st.divider()
        user = st.selectbox("เลือกชื่อผู้ใช้", users, key="overview_user")
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
        user = st.selectbox("เลือกชื่อผู้ใช้", users, key="recommend_user")
        top_n = st.slider("จำนวนคำแนะนำสูงสุด", 1, 10, 6)
        st.caption("คะแนนแนะนำ = เส้นทางความคล้าย × 3 + คะแนนรีวิวเฉลี่ย × 0.5 · ตัดรุ่นที่เคยเช่าแล้ว · เช่ารุ่นเดิมซ้ำไม่เพิ่มเส้นทางซ้ำ")
        cards(recommend(user, top_n), True)
    elif page == "ค้นหารถเช่า":
        st.subheader("🔎 ค้นหารถมอเตอร์ไซค์")
        keyword = st.text_input("ชื่อรุ่นหรือยี่ห้อ")
        cards([r for r in rows if keyword.lower() in r["name"].lower()])
    elif page == "ประวัติการเช่า / ให้คะแนน":
        st.subheader("📝 บันทึกประสบการณ์หลังเช่ารถ")
        user = st.selectbox("เลือกชื่อผู้ใช้", users, key="history_user")
        st.caption("บันทึกว่าผู้ใช้เคยเช่ารถรุ่นไหนและให้คะแนนเท่าไหร่ เพื่อนำไปใช้ในการแนะนำ")
        model = st.selectbox("รุ่นรถที่เคยเช่า", [r["name"] for r in rows])
        show_image(next(r for r in rows if r["name"] == model))
        with st.form("rental_form", clear_on_submit=True):
            rental_date = st.date_input("วันที่เคยเช่า", value=date.today(), max_value=date.today())
            rating = st.slider("คะแนนความพึงพอใจ", 1.0, 5.0, 4.0, 0.5)
            submit = st.form_submit_button("บันทึกประวัติและคะแนน", type="primary")
        if submit:
            try:
                record_rental(user, model, rental_date.isoformat(), rating)
                st.success("บันทึกแล้ว คะแนนนี้จะนำไปใช้แนะนำรถให้คนอื่น")
            except ValueError as exc:
                st.error(str(exc))
        st.subheader(f"ประวัติและคะแนนของ {user}")
        st.dataframe(pd.DataFrame(rental_history(user)), hide_index=True, use_container_width=True)
    elif page == "กราฟการเช่ารถ":
        st.subheader("📊 กราฟการเช่ารถตามผู้ใช้")
        user = st.selectbox("เลือกชื่อผู้ใช้", users, key="graph_user")
        edges = query("MATCH (u:User {name:$user})-[r:RENTED]->(m:Motorcycle) RETURN u.name AS user, m.name AS motorcycle, r.rating AS rating", {"user":user})
        if not edges:
            st.info(f"{user} ยังไม่มีประวัติการเช่ารถ")
        else:
            dot = ["digraph G {", "rankdir=LR;"]
            for edge in edges:
                dot.append(f'{json.dumps("user:"+edge["user"])} [label={json.dumps(edge["user"])} shape=ellipse];')
                dot.append(f'{json.dumps("model:"+edge["motorcycle"])} [label={json.dumps(edge["motorcycle"])} shape=box];')
                dot.append(f'{json.dumps("user:"+edge["user"])} -> {json.dumps("model:"+edge["motorcycle"])} [label="RENTED / {edge["rating"] if edge["rating"] is not None else "unrated"}"];')
            st.graphviz_chart("\n".join(dot+["}"]))
            st.dataframe(pd.DataFrame(edges), hide_index=True, use_container_width=True)

