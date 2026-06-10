# 🚀 คู่มือ Deploy BuildMaster Pro บน Render.com
## (ฟรี • ไม่ต้องตั้งค่า Server)

---

## ✅ สิ่งที่ต้องมี

| รายการ | รายละเอียด |
|--------|-----------|
| GitHub Account | github.com (ฟรี) |
| Render Account | render.com (ฟรี) |
| ไฟล์โปรเจค | buildmaster-pro.zip แตกแล้ว |

---

## ขั้นตอนที่ 1 — อัปโหลดโค้ดขึ้น GitHub

### 1.1 สร้าง Repository ใหม่

1. ไปที่ **github.com** → กด **New repository**
2. ตั้งชื่อ: `buildmaster-pro`
3. เลือก **Private** (แนะนำ เพราะมีโค้ดระบบ)
4. กด **Create repository**

### 1.2 อัปโหลดไฟล์

**วิธี A — ผ่านเว็บ GitHub (ง่ายที่สุด)**

1. กด **uploading an existing file**
2. ลากโฟลเดอร์ทั้งหมดใน `buildmaster/` วางลงในหน้าเว็บ
3. กด **Commit changes**

**วิธี B — ผ่าน Git (ถ้ามี Git ติดตั้งแล้ว)**

```bash
cd buildmaster
git init
git add .
git commit -m "Initial commit: BuildMaster Pro"
git branch -M main
git remote add origin https://github.com/USERNAME/buildmaster-pro.git
git push -u origin main
```

> ⚠️ **สำคัญ**: อย่า commit ไฟล์ `data/buildmaster.db` ขึ้น GitHub
> สร้างไฟล์ `.gitignore` ก่อน:

```
data/
static/uploads/
__pycache__/
*.pyc
*.db
logs/
*.log
```

---

## ขั้นตอนที่ 2 — สร้าง Web Service บน Render

1. ไปที่ **render.com** → Sign Up / Login
2. กด **New +** → เลือก **Web Service**
3. เลือก **Connect a repository**
4. Connect GitHub → เลือก repo `buildmaster-pro`
5. กด **Connect**

---

## ขั้นตอนที่ 3 — ตั้งค่า Web Service

กรอกข้อมูลดังนี้:

| Field | ค่าที่ใส่ |
|-------|---------|
| **Name** | `buildmaster-pro` |
| **Region** | Singapore (ใกล้ไทยที่สุด) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -c gunicorn.conf.py app:app` |
| **Instance Type** | Free |

---

## ขั้นตอนที่ 4 — ตั้งค่า Environment Variables

กด **Advanced** → **Add Environment Variable** → เพิ่ม 2 ตัวนี้:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | คลิก **Generate** ให้ Render สร้างให้อัตโนมัติ |
| `RENDER` | `true` |

---

## ขั้นตอนที่ 5 — เพิ่ม Persistent Disk (สำหรับ Database + รูปภาพ)

> ⚠️ สำคัญมาก — ถ้าไม่ทำ ข้อมูลจะหายทุกครั้งที่ Render restart

1. กด **Advanced** → **Add Disk**
2. ตั้งค่า:

| Field | ค่า |
|-------|-----|
| **Name** | `buildmaster-data` |
| **Mount Path** | `/data` |
| **Size** | `1 GB` (ฟรี tier ไม่รองรับ Disk → ใช้แผน Starter $7/เดือน) |

> 💡 **ทางเลือกฟรี**: ถ้าใช้ Free tier ข้อมูลจะ reset ทุก deploy
> แนะนำให้ใช้ Starter plan ($7/เดือน) เพื่อ persistent disk

---

## ขั้นตอนที่ 6 — Deploy!

กด **Create Web Service**

Render จะ:
1. Clone โค้ดจาก GitHub
2. รัน `pip install -r requirements.txt`
3. Start server ด้วย Gunicorn

รอประมาณ **2-5 นาที** จนเห็น **Live** สีเขียว ✅

URL จะได้มาประมาณ: `https://buildmaster-pro.onrender.com`

---

## ขั้นตอนที่ 7 — สร้าง Admin User ครั้งแรก

หลัง Deploy เสร็จ ต้องสร้าง User ก่อนใช้งานได้

1. ไปที่ Render Dashboard → Web Service ของคุณ
2. กด **Shell** (แถบด้านบน)
3. พิมพ์คำสั่ง:

```bash
python manage.py create-user
```

4. กรอก:
   - Username: `admin`
   - ชื่อแสดงผล: `สมชาย ก่อสร้าง`
   - Role: `1` (admin)
   - รหัสผ่าน: (กรอก 8+ ตัว มีตัวเลข)

5. กด Enter → เห็น ✅ = สำเร็จ

---

## ขั้นตอนที่ 8 — เข้าใช้งาน

เปิดเบราว์เซอร์ไปที่ URL ของคุณ:

```
https://buildmaster-pro.onrender.com
```

จะถูก redirect ไปหน้า Login → กรอก username/password ที่สร้างไว้

---

## 🔄 การอัปเดตโค้ด

ทุกครั้งที่ push โค้ดใหม่ขึ้น GitHub → Render จะ Deploy อัตโนมัติ:

```bash
git add .
git commit -m "Update: แก้ไข..."
git push origin main
```

---

## 🐛 แก้ปัญหาทั่วไป

### แอพไม่ขึ้น / Error 500
```
# ดู Logs ใน Render Dashboard → Logs tab
# มักเกิดจาก requirements.txt ขาดหายหรือ syntax error ใน app.py
```

### Login ไม่ได้ / ล็อกอินแล้ว redirect loop
```bash
# ใน Shell ของ Render:
python manage.py list-users    # ดู user ที่มี
python manage.py reset-password # รีเซ็ตรหัสผ่าน
```

### รูปภาพหาย
```
# เกิดจาก Disk ไม่ได้ mount หรือใช้ Free plan
# ตรวจสอบใน Render Dashboard → Disks
```

### แอพช้า / หยุดทำงาน (Free Tier)
```
Free tier จะ sleep หลังไม่มีการใช้งาน 15 นาที
→ ครั้งแรกที่เปิดจะช้า 30-60 วินาที (Cold Start)
→ แก้: อัปเกรดเป็น Starter plan ($7/เดือน)
```

---

## 💰 ราคา Render

| Plan | ราคา | RAM | Disk | Cold Start |
|------|------|-----|------|------------|
| **Free** | ฟรี | 512MB | ❌ | ✅ (ช้า) |
| **Starter** | $7/เดือน | 512MB | ✅ 1GB | ❌ |
| **Standard** | $25/เดือน | 2GB | ✅ | ❌ |

สำหรับใช้งานจริง แนะนำ **Starter** ($7/เดือน)

---

## 🔐 Security Checklist

- [x] SECRET_KEY เป็น random จาก Render
- [x] ไม่ได้ commit .db หรือ .env ขึ้น GitHub
- [x] User สร้างผ่าน CLI เท่านั้น
- [ ] (แนะนำ) เพิ่ม Custom Domain + HTTPS

---

*BuildMaster Pro — Deploy Guide for Render.com*
