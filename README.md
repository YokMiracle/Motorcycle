# รวมการบ้าน — 664245008

ณัฏฐนันท์ เกียรติจิรยาดา
Steam URL: https://motorcycle-gvxn2krgpgs76foizvr8nu.streamlit.app/recommendation

รวมการบ้านทั้ง 3 ไฟล์ที่แนบมา พร้อมไฟล์ประกอบโปรเจกต์มอเตอร์ไซค์

[หน้า index](index.html) · [Repository](https://github.com/YokMiracle/Motorcycle)

| งาน | การบ้าน | ไฟล์ | Colab |
| --- | --- | --- | --- |
| 01 | ระบบชมรมด้วย Neo4j | [เปิดไฟล์](homework/664245008_club_system.pdf) | — |
| 02 | Motorcycle Recommender ด้วย Graph | [เปิดไฟล์](homework/664245008_Motorcycle_RecommenderSystem.ipynb) | [เปิด Colab](https://colab.research.google.com/github/YokMiracle/Motorcycle/blob/main/homework/664245008_Motorcycle_RecommenderSystem.ipynb) |
| 03 | Motorcycle Recommender ด้วย Neo4j | [เปิดไฟล์](homework/CryptoRecommender_664245008_Neo4j.ipynb) | [เปิด Colab](https://colab.research.google.com/github/YokMiracle/Motorcycle/blob/main/homework/CryptoRecommender_664245008_Neo4j.ipynb) |

ไฟล์ `CryptoRecommender_664245008_Neo4j.ipynb` มีเนื้อหาเกี่ยวกับมอเตอร์ไซค์ จึงใช้ชื่องานตามเนื้อหา โดยเก็บไฟล์ต้นฉบับไว้ครบถ้วน

## โน้ตบุ๊กประกอบโปรเจกต์เดิม

- [โครงสร้างข้อมูล](notebooks/01_motorcycle_data_structure.ipynb)
- [วิเคราะห์ความสัมพันธ์](notebooks/02_motorcycle_relationship_analysis.ipynb)
- [ระบบแนะนำฉบับรวม](MotorcycleRecommender_664245008_Neo4j.ipynb)

# MotoGraph — Motorcycle Graph Recommendation

เวอร์ชันนี้ปรับระบบจากแนว “ประวัติการเช่า” เป็นระบบแนะนำจาก “ความชอบ” ให้ทำงานในแนวเดียวกับ Graph Recommendation โดยยังใช้ข้อมูลมอเตอร์ไซค์เดิมของโปรเจกต์

## การทำงาน
1. เลือกผู้ใช้ในหน้า **ภาพรวม** เพื่อดูความชอบและสถิติ
2. หน้า **แนะนำสำหรับคุณ** ใช้เส้นทาง `User -> LIKES -> Motorcycle <- LIKES - User -> LIKES -> Motorcycle` เพื่อหารุ่นใหม่
3. หน้า **บันทึกความชอบ** เพิ่ม/อัปเดตความสัมพันธ์ `LIKES` พร้อมคะแนน 1–5
4. หน้า **ประวัติความชอบ** แสดงตาราง สถิติ และกราฟคะแนนของผู้ใช้
5. หน้า **กราฟความสัมพันธ์** แสดง Neo4j graph รายคนหรือทั้งหมด
6. หน้า **จัดการข้อมูล** เพิ่ม/ลบผู้ใช้ เพิ่ม/ลบรถ และอัปโหลด/แก้ไขรูปรถ

ระบบจะคัดลอกข้อมูล `RENTED` จากเวอร์ชันเก่าเข้า `LIKES` อัตโนมัติ เพื่อรักษาข้อมูลเดิมไว้

## วิธีรัน
```bash
pip install -r requirements.txt
streamlit run app.py
```

คัดลอก `.streamlit/secrets.toml.example` เป็น `.streamlit/secrets.toml` แล้วกรอก Neo4j URI / username / password ก่อนรัน
