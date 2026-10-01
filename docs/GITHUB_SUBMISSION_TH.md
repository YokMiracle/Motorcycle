# นำงานขึ้น GitHub

ชุดนี้รวมการบ้านที่แนบมา 3 ไฟล์ใน homework/ (PDF 1 ไฟล์ และโน้ตบุ๊ก 2 ไฟล์) พร้อมลิงก์ใน README, index.html และหน้ารวม Streamlit รวมถึงโน้ตบุ๊กเดิมอีก 3 ไฟล์

1. แตก ZIP แล้วคัดลอกไฟล์ภายใน Motorcycle ไปยังโฟลเดอร์ repository เดิม ชุดนี้ไม่มี .git จึงไม่ทับประวัติ Git
2. เปิด PowerShell ในโฟลเดอร์ Motorcycle เดิม แล้วตรวจ branch และ remote ก่อนอัปโหลด:

```powershell
git switch main
git remote -v
git status
git add .
git diff --cached --stat
git commit -m "Add homework index and notebook links"
git push origin main
```

Remote ที่ใช้ในสารบัญคือ https://github.com/YokMiracle/Motorcycle.git
ไม่ต้องเพิ่ม secrets.toml, .env หรือรหัสผ่านขึ้น GitHub

README จะแสดงสารบัญเมื่อเปิด repository ส่วน index.html เป็นหน้า HTML สำหรับเปิดในเครื่องหรือเผยแพร่ผ่าน GitHub Pages; การอัปโหลดไฟล์อย่างเดียวไม่ได้เปิด GitHub Pages อัตโนมัติ
