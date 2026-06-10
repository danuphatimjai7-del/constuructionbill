#!/usr/bin/env python3
"""
BuildMaster Pro — Management CLI
ใช้จัดการผู้ใช้งานจากหลังบ้านเท่านั้น

คำสั่งที่ใช้ได้:
  python manage.py create-user          สร้างผู้ใช้ใหม่ (แบบ interactive)
  python manage.py list-users           แสดงผู้ใช้ทั้งหมด
  python manage.py reset-password       รีเซ็ตรหัสผ่าน
  python manage.py deactivate-user      ปิดการใช้งานผู้ใช้
  python manage.py activate-user        เปิดการใช้งานผู้ใช้
  python manage.py delete-user          ลบผู้ใช้ถาวร
"""

import sys, os, sqlite3, secrets, hashlib, getpass, datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "buildmaster.db")

ROLES = {
    "1": ("admin",   "ผู้ดูแลระบบ — เข้าถึงได้ทุกส่วน"),
    "2": ("manager", "ผู้จัดการ   — จัดการโครงการ/แรงงาน/การเงิน"),
    "3": ("viewer",  "ผู้ดู       — ดูข้อมูลได้อย่างเดียว"),
}

# ─── COLORS ───
R  = "\033[91m"  # red
G  = "\033[92m"  # green
Y  = "\033[93m"  # yellow
B  = "\033[94m"  # blue
C  = "\033[96m"  # cyan
W  = "\033[97m"  # white
DIM= "\033[2m"
RST= "\033[0m"
BOLD="\033[1m"

def banner():
    print(f"""
{Y}╔══════════════════════════════════════════════╗
║  {W}{BOLD}🏗  BuildMaster Pro — Management CLI{RST}{Y}         ║
║  {DIM}จัดการผู้ใช้งานระบบ (Admin Only){RST}{Y}             ║
╚══════════════════════════════════════════════╝{RST}""")

def get_db():
    if not os.path.exists(DB_PATH):
        print(f"{R}❌ ไม่พบฐานข้อมูล กรุณารัน: python app.py ก่อน{RST}")
        sys.exit(1)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000)
    return salt, hashed.hex()

def validate_password(pw):
    errors = []
    if len(pw) < 8:          errors.append("ต้องมีอย่างน้อย 8 ตัวอักษร")
    if not any(c.isdigit() for c in pw):   errors.append("ต้องมีตัวเลขอย่างน้อย 1 ตัว")
    if not any(c.isalpha() for c in pw):   errors.append("ต้องมีตัวอักษรอย่างน้อย 1 ตัว")
    return errors

def input_password(label="รหัสผ่าน"):
    while True:
        pw = getpass.getpass(f"  {label}: ")
        errs = validate_password(pw)
        if errs:
            for e in errs:
                print(f"  {R}✗ {e}{RST}")
            continue
        pw2 = getpass.getpass(f"  ยืนยันรหัสผ่านอีกครั้ง: ")
        if pw != pw2:
            print(f"  {R}✗ รหัสผ่านไม่ตรงกัน{RST}")
            continue
        return pw

# ══════════════════════════════════════════
#  CREATE USER
# ══════════════════════════════════════════
def cmd_create_user():
    print(f"\n{C}━━━ สร้างผู้ใช้งานใหม่ ━━━{RST}\n")
    db = get_db()

    # Username
    while True:
        username = input(f"  ชื่อผู้ใช้ (username): ").strip().lower()
        if not username:
            print(f"  {R}✗ กรุณากรอกชื่อผู้ใช้{RST}"); continue
        if not username.replace("_","").replace("-","").isalnum():
            print(f"  {R}✗ ใช้ได้เฉพาะ a-z, 0-9, _, -{RST}"); continue
        exists = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if exists:
            print(f"  {R}✗ ชื่อผู้ใช้ '{username}' มีอยู่แล้ว{RST}"); continue
        break

    # Display name
    display_name = input(f"  ชื่อแสดงผล (ภาษาไทยได้): ").strip()
    if not display_name: display_name = username

    # Role
    print(f"\n  {W}เลือก Role:{RST}")
    for k, (role, desc) in ROLES.items():
        print(f"    {Y}[{k}]{RST} {desc}")
    while True:
        choice = input("  เลือก [1/2/3]: ").strip()
        if choice in ROLES: break
        print(f"  {R}✗ กรุณาเลือก 1, 2 หรือ 3{RST}")
    role = ROLES[choice][0]

    # Password
    print()
    password = input_password()

    # Confirm
    print(f"""
  {DIM}─────────────────────────────{RST}
  {W}ยืนยันข้อมูล:{RST}
    Username    : {G}{username}{RST}
    ชื่อแสดงผล : {display_name}
    Role        : {Y}{role}{RST}
  {DIM}─────────────────────────────{RST}""")
    confirm = input("  บันทึกผู้ใช้นี้? [y/N]: ").strip().lower()
    if confirm != "y":
        print(f"  {Y}ยกเลิก{RST}"); return

    salt, pw_hash = hash_password(password)
    db.execute("""INSERT INTO users (username, display_name, role, salt, password_hash)
        VALUES (?, ?, ?, ?, ?)""", (username, display_name, role, salt, pw_hash))
    db.commit()
    db.close()
    print(f"\n  {G}✅ สร้างผู้ใช้ '{username}' สำเร็จ!{RST}")
    print(f"  เข้าสู่ระบบที่: {C}http://localhost:5000/login{RST}\n")

# ══════════════════════════════════════════
#  LIST USERS
# ══════════════════════════════════════════
def cmd_list_users():
    print(f"\n{C}━━━ รายชื่อผู้ใช้ทั้งหมด ━━━{RST}\n")
    db = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at").fetchall()
    db.close()
    if not users:
        print(f"  {Y}ยังไม่มีผู้ใช้ สร้างด้วย: python manage.py create-user{RST}\n")
        return
    fmt = f"  {{:<4}} {{:<20}} {{:<20}} {{:<10}} {{:<10}} {{:<20}}"
    print(fmt.format("ID", "Username", "ชื่อแสดงผล", "Role", "สถานะ", "เข้าระบบล่าสุด"))
    print(f"  {'─'*85}")
    for u in users:
        status = f"{G}เปิด{RST}" if u["is_active"] else f"{R}ปิด{RST}"
        last   = u["last_login"] or "ยังไม่เคย"
        role_c = Y if u["role"] == "admin" else (C if u["role"] == "manager" else W)
        print(fmt.format(
            str(u["id"]), u["username"], u["display_name"] or "—",
            f"{role_c}{u['role']}{RST}", status, last
        ))
    print()

# ══════════════════════════════════════════
#  RESET PASSWORD
# ══════════════════════════════════════════
def cmd_reset_password():
    print(f"\n{C}━━━ รีเซ็ตรหัสผ่าน ━━━{RST}\n")
    db = get_db()
    username = input("  Username ที่ต้องการรีเซ็ต: ").strip().lower()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        print(f"  {R}✗ ไม่พบผู้ใช้ '{username}'{RST}\n"); db.close(); return
    print(f"  พบผู้ใช้: {G}{user['display_name'] or username}{RST} (role: {user['role']})")
    print()
    password = input_password("รหัสผ่านใหม่")
    salt, pw_hash = hash_password(password)
    db.execute("UPDATE users SET salt=?, password_hash=? WHERE username=?", (salt, pw_hash, username))
    db.commit(); db.close()
    print(f"\n  {G}✅ รีเซ็ตรหัสผ่านของ '{username}' สำเร็จ{RST}\n")

# ══════════════════════════════════════════
#  DEACTIVATE / ACTIVATE
# ══════════════════════════════════════════
def cmd_toggle_user(activate=False):
    action = "เปิด" if activate else "ปิด"
    print(f"\n{C}━━━ {action}การใช้งานผู้ใช้ ━━━{RST}\n")
    db = get_db()
    username = input(f"  Username ที่ต้องการ{action}: ").strip().lower()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        print(f"  {R}✗ ไม่พบผู้ใช้ '{username}'{RST}\n"); db.close(); return
    new_val = 1 if activate else 0
    db.execute("UPDATE users SET is_active=? WHERE username=?", (new_val, username))
    db.commit(); db.close()
    icon = G if activate else R
    print(f"\n  {icon}✅ {action}การใช้งาน '{username}' สำเร็จ{RST}\n")

# ══════════════════════════════════════════
#  DELETE USER
# ══════════════════════════════════════════
def cmd_delete_user():
    print(f"\n{C}━━━ ลบผู้ใช้ถาวร ━━━{RST}\n")
    db = get_db()
    username = input("  Username ที่ต้องการลบ: ").strip().lower()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        print(f"  {R}✗ ไม่พบผู้ใช้ '{username}'{RST}\n"); db.close(); return
    print(f"  {R}⚠️  คำเตือน: การลบไม่สามารถยกเลิกได้!{RST}")
    print(f"  จะลบผู้ใช้: {W}{user['display_name'] or username}{RST}")
    confirm = input("  พิมพ์ DELETE เพื่อยืนยัน: ").strip()
    if confirm != "DELETE":
        print(f"  {Y}ยกเลิก{RST}\n"); db.close(); return
    db.execute("DELETE FROM users WHERE username=?", (username,))
    db.commit(); db.close()
    print(f"\n  {G}✅ ลบผู้ใช้ '{username}' เรียบร้อยแล้ว{RST}\n")

# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════
COMMANDS = {
    "create-user":    (cmd_create_user,                "สร้างผู้ใช้ใหม่"),
    "list-users":     (cmd_list_users,                 "แสดงผู้ใช้ทั้งหมด"),
    "reset-password": (cmd_reset_password,             "รีเซ็ตรหัสผ่าน"),
    "deactivate-user":(lambda: cmd_toggle_user(False), "ปิดการใช้งานผู้ใช้"),
    "activate-user":  (lambda: cmd_toggle_user(True),  "เปิดการใช้งานผู้ใช้"),
    "delete-user":    (cmd_delete_user,                "ลบผู้ใช้ถาวร"),
}

if __name__ == "__main__":
    banner()
    if len(sys.argv) < 2:
        print(f"\n{W}คำสั่งที่ใช้ได้:{RST}")
        for cmd, (fn, desc) in COMMANDS.items():
            print(f"  {Y}python manage.py {cmd:<20}{RST} {desc}")
        print()
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"\n  {R}✗ ไม่รู้จักคำสั่ง '{cmd}'{RST}")
        print(f"  ใช้ {Y}python manage.py{RST} เพื่อดูคำสั่งทั้งหมด\n")
        sys.exit(1)
    try:
        COMMANDS[cmd][0]()
    except KeyboardInterrupt:
        print(f"\n\n  {Y}ยกเลิกการดำเนินการ{RST}\n")
