# 🚂 คู่มือ Deploy BuildMaster Pro บน Railway
## (ฟรี $5 เครดิต/เดือน • รองรับ Persistent Volume • ไม่ Sleep)

---

## ✅ สิ่งที่ต้องมี

| รายการ | รายละเอียด |
|--------|-----------|
| GitHub Account | github.com (ฟรี) |
| Railway Account | railway.app (ฟรี — $5 credit/เดือน) |
| ไฟล์โปรเจค | buildmaster-pro.zip แตกแล้ว |

---

## ขั้นตอนที่ 1 — อัปโหลดโค้ดขึ้น GitHub

### 1.1 สร้าง Repository ใหม่

1. ไปที่ **github.com** → กด **New repository**
2. ชื่อ: `buildmaster-pro`
3. เลือก **Private**
4. กด **Create repository**

### 1.2 อัปโหลดไฟล์

**วิธีง่าย — ลากไฟล์ผ่านเว็บ:**
1. กด **"uploading an existing file"**
2. ลากไฟล์ทั้งหมดในโฟลเดอร์ `buildmaster/` วางลง
3. กด **Commit changes**

**หรือใช้ Git:**
```bash
cd buildmaster
git init
git add .
git commit -m "Initial commit: BuildMaster Pro"
git branch -M main
git remote add origin https://github.com/USERNAME/buildmaster-pro.git
git push -u origin main
```

---

## ขั้นตอนที่ 2 — สร้างโปรเจคบน Railway

1. ไปที่ **railway.app** → Sign Up ด้วย GitHub
2. กด **New Project**
3. เลือก **Deploy from GitHub repo**
4. เลือก repo `buildmaster-pro`
5. Railway จะเริ่ม deploy อัตโนมัติ (รอ ~2 นาที)

---

## ขั้นตอนที่ 3 — ตั้งค่า Environment Variables

ใน Railway Dashboard → เลือก Service → แท็บ **Variables** → กด **New Variable**

| Key | Value | หมายเหตุ |
|-----|-------|---------|
| `SECRET_KEY` | (กด Generate Random) | สำหรับ Flask Session |
| `DATA_DIR` | `/data` | Path สำหรับ DB + รูปภาพ |

---

## ขั้นตอนที่ 4 — เพิ่ม Volume (Persistent Storage)

1. ใน Railway Dashboard → กด **+ New** → **Volume**
2. ตั้งค่า:
   - **Mount Path**: `/data`
3. Railway จะ attach volume เข้ากับ Service อัตโนมัติ
4. กด **Deploy** อีกครั้งเพื่อ apply การเปลี่ยนแปลง

---

## ขั้นตอนที่ 5 — สร้าง Domain

1. แท็บ **Settings** → **Networking** → **Generate Domain**
2. จะได้ URL ประมาณ: `buildmaster-pro.up.railway.app`

---

## ขั้นตอนที่ 6 — สร้าง Admin User

1. ใน Railway Dashboard → แท็บ **Deploy** → กด **Railway CLI** หรือใช้ **Shell**
2. รันคำสั่ง:

```bash
python manage.py create-user
```

3. กรอกข้อมูล:
   - username: `admin`
   - display name: ชื่อของคุณ
   - role: `1` (admin)
   - password: รหัสผ่าน 8+ ตัวอักษร

---

## ขั้นตอนที่ 7 — เข้าใช้งาน

เปิดเบราว์เซอร์:
```
https://YOUR-APP.up.railway.app
```

---

## 🔄 อัปเดตโค้ด

```bash
git add .
git commit -m "Update: ..."
git push origin main
# Railway deploy อัตโนมัติภายใน 2-3 นาที
```

---

## 💰 ราคา Railway

| Plan | ราคา | RAM | Volume | หมายเหตุ |
|------|------|-----|--------|---------|
| **Hobby** | ฟรี $5 credit/เดือน | 512MB | ✅ | เพียงพอสำหรับใช้งานเบา |
| **Pro** | $20/เดือน | ไม่จำกัด | ✅ | สำหรับ Production |

$5 credit ครอบคลุมการใช้งานประมาณ 500 ชั่วโมง/เดือน

---

## 🐛 แก้ปัญหาที่พบบ่อย

| ปัญหา | วิธีแก้ |
|-------|---------|
| Build Failed | ดู Logs → ตรวจ `requirements.txt` |
| 502 Error | Service ยังไม่ start → รอสักครู่ |
| Login ไม่ได้ | รัน `python manage.py create-user` ใน Shell |
| ข้อมูลหาย | ตรวจสอบว่า Volume mount ที่ `/data` แล้ว |

---

*BuildMaster Pro — Railway Deployment Guide*
