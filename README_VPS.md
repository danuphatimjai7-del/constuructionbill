# 🚀 คู่มือติดตั้ง BuildMaster Pro บน VPS
## (Ubuntu 20.04 / 22.04 LTS)

---

## 📋 สิ่งที่ต้องเตรียม

| รายการ | รายละเอียด |
|--------|-----------|
| VPS    | RAM ≥ 1GB, Disk ≥ 10GB (DigitalOcean / Vultr / AWS Lightsail) |
| OS     | Ubuntu 20.04 หรือ 22.04 LTS |
| โดเมน | (ไม่จำเป็น แต่แนะนำถ้าต้องการ HTTPS) |
| SSH    | เข้าถึงเซิร์ฟเวอร์ได้ |

---

## ขั้นตอนที่ 1 — เชื่อมต่อ VPS

```bash
ssh root@YOUR_VPS_IP
```

---

## ขั้นตอนที่ 2 — อัปเดตระบบ + ติดตั้ง Python

```bash
# อัปเดต package list
sudo apt update && sudo apt upgrade -y

# ติดตั้ง Python, pip, nginx, git
sudo apt install -y python3 python3-pip python3-venv nginx git curl

# ตรวจสอบเวอร์ชัน
python3 --version    # ควรได้ Python 3.8+
nginx -v
```

---

## ขั้นตอนที่ 3 — สร้าง User สำหรับรันแอพ (แนะนำ)

```bash
# สร้าง user ชื่อ buildmaster (ปลอดภัยกว่ารันด้วย root)
sudo useradd -m -s /bin/bash buildmaster
sudo mkdir -p /var/www/buildmaster
sudo chown buildmaster:buildmaster /var/www/buildmaster
```

---

## ขั้นตอนที่ 4 — อัปโหลดไฟล์แอพ

**วิธีที่ 1: ใช้ SCP จากเครื่องตัวเอง**
```bash
# รันบนเครื่องตัวเอง (ไม่ใช่ VPS)
scp buildmaster-pro.zip root@YOUR_VPS_IP:/var/www/buildmaster/
```

**วิธีที่ 2: ใช้ wget (ถ้าอัปโหลดไฟล์ขึ้น cloud ก่อน)**
```bash
cd /var/www/buildmaster
wget https://your-link.com/buildmaster-pro.zip
```

**แตกไฟล์**
```bash
cd /var/www/buildmaster
sudo apt install -y unzip
unzip buildmaster-pro.zip
mv buildmaster/* .
rm -rf buildmaster buildmaster-pro.zip
```

โครงสร้างที่ถูกต้อง:
```
/var/www/buildmaster/
├── app.py
├── manage.py
├── requirements.txt
├── gunicorn.conf.py
├── templates/
├── static/
├── data/
└── logs/
```

---

## ขั้นตอนที่ 5 — สร้าง Virtual Environment + ติดตั้ง Dependencies

```bash
cd /var/www/buildmaster

# สร้าง virtual environment
python3 -m venv venv

# เปิดใช้งาน venv
source venv/bin/activate

# ติดตั้ง packages
pip install -r requirements.txt

# ตรวจสอบ
pip list | grep -E "Flask|gunicorn"
```

---

## ขั้นตอนที่ 6 — ตั้งค่า SECRET_KEY

```bash
# สร้าง SECRET_KEY แบบสุ่ม (สำคัญมาก!)
python3 -c "import secrets; print(secrets.token_hex(32))"
# จะได้ค่าประมาณ: a3f9e2b1c4d5...

# เปิดไฟล์ service
sudo nano /etc/systemd/system/buildmaster.service
```

วางเนื้อหาต่อไปนี้ (แก้ค่าที่ระบุ):

```ini
[Unit]
Description=BuildMaster Pro Web Application
After=network.target

[Service]
Type=simple
User=buildmaster
WorkingDirectory=/var/www/buildmaster
Environment="SECRET_KEY=ใส่ค่าจากคำสั่งข้างบน"
ExecStart=/var/www/buildmaster/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## ขั้นตอนที่ 7 — สร้างผู้ใช้คนแรก (Admin)

```bash
cd /var/www/buildmaster
source venv/bin/activate

# สร้างฐานข้อมูล (รันครั้งแรก)
python3 -c "from app import init_db; init_db(); print('DB ready')"

# สร้าง Admin user
python3 manage.py create-user
# กรอก: username, ชื่อแสดงผล, เลือก Role 1 (admin), ตั้งรหัสผ่าน
```

ตัวอย่างการสร้าง User เพิ่มเติม:
```bash
# สร้าง manager
python3 manage.py create-user
# ใส่ข้อมูล → เลือก Role 2 (manager)

# ดูรายชื่อ user ทั้งหมด
python3 manage.py list-users

# รีเซ็ตรหัสผ่าน
python3 manage.py reset-password

# ปิดการใช้งาน user
python3 manage.py deactivate-user
```

---

## ขั้นตอนที่ 8 — เริ่ม Service

```bash
# โหลด systemd config ใหม่
sudo systemctl daemon-reload

# เปิดใช้งานตอน boot
sudo systemctl enable buildmaster

# เริ่ม service
sudo systemctl start buildmaster

# ตรวจสอบสถานะ
sudo systemctl status buildmaster
```

✅ ถ้าเห็น `Active: active (running)` = สำเร็จ

---

## ขั้นตอนที่ 9 — ตั้งค่า Nginx (Reverse Proxy)

```bash
# สร้างไฟล์ config
sudo nano /etc/nginx/sites-available/buildmaster
```

วางเนื้อหา:

```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;   # หรือ yourdomain.com

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
        client_max_body_size 10M;
    }

    location /static/ {
        alias /var/www/buildmaster/static/;
        expires 30d;
    }
}
```

```bash
# เปิดใช้งาน config
sudo ln -s /etc/nginx/sites-available/buildmaster /etc/nginx/sites-enabled/

# ลบ default config (ถ้ามี)
sudo rm -f /etc/nginx/sites-enabled/default

# ทดสอบ config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## ขั้นตอนที่ 10 — ติดตั้ง SSL (HTTPS) ฟรีด้วย Let's Encrypt

> ⚠️ ต้องมีโดเมนชี้มาที่ IP ของ VPS ก่อน

```bash
# ติดตั้ง certbot
sudo apt install -y certbot python3-certbot-nginx

# ขอ certificate (แทน yourdomain.com ด้วยโดเมนจริง)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# ต่ออายุอัตโนมัติ (ทดสอบ)
sudo certbot renew --dry-run
```

---

## ขั้นตอนที่ 11 — ตั้งค่า Firewall

```bash
# เปิด port ที่จำเป็น
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# เปิด firewall
sudo ufw enable

# ตรวจสอบ
sudo ufw status
```

---

## 🔧 คำสั่งจัดการ Service ประจำวัน

```bash
# ดู log แบบ real-time
sudo journalctl -u buildmaster -f

# Restart แอพ (หลังแก้ไขโค้ด)
sudo systemctl restart buildmaster

# ดู log เฉพาะ error
sudo journalctl -u buildmaster -p err --since "1 hour ago"

# ดู access log ของ nginx
sudo tail -f /var/log/nginx/access.log

# ดูการใช้ RAM/CPU
htop
```

---

## 🔄 วิธีอัปเดตแอพ

```bash
cd /var/www/buildmaster

# อัปโหลดไฟล์ใหม่แล้ว restart
sudo systemctl restart buildmaster

# หรือถ้าแก้ไข requirements.txt ด้วย
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart buildmaster
```

---

## 💾 การ Backup ฐานข้อมูล

```bash
# Backup ด้วยตนเอง
cp /var/www/buildmaster/data/buildmaster.db \
   /backup/buildmaster_$(date +%Y%m%d_%H%M%S).db

# ตั้ง cron job backup ทุกวัน 02:00
sudo crontab -e
# เพิ่มบรรทัด:
# 0 2 * * * cp /var/www/buildmaster/data/buildmaster.db /backup/buildmaster_$(date +\%Y\%m\%d).db
```

---

## 🐛 แก้ปัญหาทั่วไป

| ปัญหา | วิธีแก้ |
|-------|---------|
| `502 Bad Gateway` | `sudo systemctl restart buildmaster` |
| แอพไม่เริ่ม | `sudo journalctl -u buildmaster -n 50` ดู error |
| ล็อกอินไม่ได้ | `python3 manage.py list-users` ตรวจสอบ user |
| รหัสผ่านลืม | `python3 manage.py reset-password` |
| DB เสียหาย | restore จาก backup |
| nginx error | `sudo nginx -t` ตรวจสอบ config |

---

## 📊 ข้อมูล Performance คาดการณ์

| ผู้ใช้พร้อมกัน | RAM ที่ใช้ | VPS ที่แนะนำ |
|----------------|----------|--------------|
| 1-5 คน         | ~150MB   | 1GB RAM      |
| 5-20 คน        | ~300MB   | 2GB RAM      |
| 20-50 คน       | ~600MB   | 4GB RAM      |

---

## 🔐 Security Checklist

- [x] ใช้ HTTPS (Let's Encrypt)
- [x] SECRET_KEY เป็น random string
- [x] รัน app ด้วย non-root user
- [x] Firewall เปิดเฉพาะ port 80, 443, 22
- [ ] เปลี่ยน SSH port (ไม่บังคับ)
- [ ] ตั้ง fail2ban ป้องกัน brute force

---

*BuildMaster Pro v1.0 — คู่มือ VPS Deployment*
