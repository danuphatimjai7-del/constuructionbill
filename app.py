"""
BuildMaster Pro — Backend API (Flask + SQLite)
รัน: python app.py
เข้าใช้งาน: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory, g, session, redirect, url_for
import base64, mimetypes
import sqlite3, os, datetime, json, hashlib, secrets, functools

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
# Cloud-compatible paths:
# - Railway/Render: set DATA_DIR env var to volume mount path (e.g. /data)
# - Local dev: uses ./data folder next to app.py
_DATA_DIR     = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
UPLOAD_FOLDER = os.path.join(_DATA_DIR, "uploads")
DB_PATH       = os.path.join(_DATA_DIR, "buildmaster.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(_DATA_DIR, exist_ok=True)
MAX_PHOTO_MB = 8

# ══════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db: db.close()

def query(sql, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(sql, args)
    if commit:
        db.commit()
        return cur.lastrowid
    rows = cur.fetchone() if one else cur.fetchall()
    return [dict(r) for r in rows] if not one else (dict(rows) if rows else None)

# ══════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310000)
    return salt, hashed.hex()

def verify_password(password, salt, stored_hash):
    _, attempt = hash_password(password, salt)
    return secrets.compare_digest(attempt, stored_hash)

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════
#  DATABASE INIT
# ══════════════════════════════════════════
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        display_name TEXT,
        role TEXT DEFAULT 'viewer',
        salt TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        last_login TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        client TEXT NOT NULL,
        project_type TEXT DEFAULT 'อาคาร/คอนโด',
        location TEXT,
        value REAL DEFAULT 0,
        progress INTEGER DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'เริ่มต้น',
        note TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        wage REAL DEFAULT 0,
        phone TEXT,
        id_card TEXT,
        status TEXT DEFAULT 'เข้างาน',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        unit TEXT DEFAULT 'หน่วย',
        quantity REAL DEFAULT 0,
        min_quantity REAL DEFAULT 0,
        price_per_unit REAL DEFAULT 0,
        supplier TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        serial_no TEXT,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        status TEXT DEFAULT 'ว่าง',
        note TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        type TEXT NOT NULL,
        category TEXT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        tx_date TEXT DEFAULT (date('now','localtime')),
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS safety_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        description TEXT NOT NULL,
        severity TEXT DEFAULT 'เล็กน้อย',
        inc_date TEXT DEFAULT (date('now','localtime')),
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS boq_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        item_no TEXT,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        unit TEXT DEFAULT 'งาน',
        quantity REAL DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total_price REAL DEFAULT 0,
        progress_pct INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS progress_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        boq_item_id INTEGER REFERENCES boq_items(id) ON DELETE SET NULL,
        reported_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        report_date TEXT DEFAULT (date('now','localtime')),
        title TEXT NOT NULL,
        description TEXT,
        progress_pct INTEGER DEFAULT 0,
        weather TEXT DEFAULT 'แจ่มใส',
        workers_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'รอตรวจสอบ',
        reviewer_note TEXT,
        reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS report_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL REFERENCES progress_reports(id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        caption TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    """)

    # Seed demo data if empty
    cur = db.execute("SELECT COUNT(*) as n FROM projects")
    if cur.fetchone()[0] == 0:
        db.executescript("""
        INSERT INTO projects (name,client,project_type,location,value,progress,start_date,end_date,status) VALUES
            ('คอนโด The River','บ.ริมน้ำพัฒนา','อาคาร/คอนโด','กรุงเทพฯ',45000000,72,'2025-01-01','2025-09-30','กำลังก่อสร้าง'),
            ('โรงงาน ABC อินดัสทรี','บ.เอบีซี อินดัส','โรงงาน','ชลบุรี',28000000,45,'2025-02-01','2025-12-31','ตามแผน'),
            ('ถนน ทล.304 กม.45-60','กรมทางหลวง','ถนน/ทางหลวง','นครราชสีมา',120000000,88,'2024-12-01','2025-05-01','ล่าช้า'),
            ('สะพานข้ามแม่น้ำ','อบจ. อยุธยา','สะพาน','อยุธยา',85000000,18,'2025-03-01','2026-02-28','เริ่มต้น');
        INSERT INTO workers (name,role,project_id,wage,phone,status) VALUES
            ('สมศักดิ์ แข็งแรง','ช่างเหล็ก',1,650,'081-111-1111','เข้างาน'),
            ('วิชัย ขยันงาน','โฟร์แมน',2,900,'082-222-2222','เข้างาน'),
            ('นิด สวยงาม','ช่างไฟฟ้า',3,750,'083-333-3333','ลาป่วย'),
            ('ประสิทธิ์ มือทอง','ช่างปูน',4,600,'084-444-4444','OT'),
            ('สุรชัย เก่งกาจ','วิศวกรโยธา',1,1500,'085-555-5555','เข้างาน');
        INSERT INTO materials (name,unit,quantity,min_quantity,price_per_unit,supplier) VALUES
            ('ปูนซีเมนต์ SCG','ถุง',42,200,145,'SCG Trading'),
            ('เหล็กเส้น DB12','ตัน',0.8,5,22500,'เหล็กไทย'),
            ('ทรายหยาบ','ลบ.ม.',15,30,380,'ทรายนำเข้า'),
            ('อิฐมอญ','ก้อน',1200,500,3.5,'อิฐบึงกุ่ม'),
            ('ไม้แบบ 3/8','แผ่น',340,100,185,'ไม้อัดไทย'),
            ('สีน้ำ Beger','ถัง',28,10,1250,'Beger Paint');
        INSERT INTO equipment (name,serial_no,project_id,status) VALUES
            ('รถแบ็กโฮ CAT 320','กข-1234',1,'ใช้งาน'),
            ('ปั้นจั่นหอ 20t','CRN-2023-001',1,'ใช้งาน'),
            ('รถมิกเซอร์ 6ล้อ','งง-5678',NULL,'ซ่อมบำรุง'),
            ('รถบดถนน BOMAG','ดด-9012',3,'ใช้งาน'),
            ('เครื่องปั่นไฟ 50KVA','GEN-789',NULL,'เสีย');
        INSERT INTO transactions (project_id,type,category,description,amount,tx_date) VALUES
            (1,'income','ค่างวด','รับเงินงวดที่ 3',1500000,'2025-06-03'),
            (2,'expense','วัสดุ','ค่าวัสดุ-เหล็กเส้น',-245000,'2025-06-02'),
            (3,'expense','ค่าแรง','ค่าแรงงานประจำเดือน',-380000,'2025-06-01'),
            (2,'income','ค่างวด','รับเงินงวดที่ 2',800000,'2025-05-31'),
            (4,'expense','เครื่องจักร','ค่าเช่าเครื่องจักร',-95000,'2025-05-30');
        INSERT INTO safety_incidents (project_id,description,severity,inc_date) VALUES
            (3,'แขนถูกกดทับเล็กน้อย','เล็กน้อย','2025-06-02'),
            (1,'วัสดุร่วงกระทบพื้น','Near Miss','2025-04-15');

        INSERT INTO boq_items (project_id,item_no,category,description,unit,quantity,unit_price,total_price,progress_pct,sort_order) VALUES
            (1,'1','งานโครงสร้าง','งานเสาเข็ม','ต้น',120,15000,1800000,100,1),
            (1,'2','งานโครงสร้าง','งานฐานราก','ลบ.ม.',450,4500,2025000,95,2),
            (1,'3','งานโครงสร้าง','งานเสา คสล.','ลบ.ม.',380,5500,2090000,80,3),
            (1,'4','งานโครงสร้าง','งานคาน-พื้น','ลบ.ม.',620,4800,2976000,65,4),
            (1,'5','งานสถาปัตย์','งานก่ออิฐ-ฉาบปูน','ตร.ม.',2800,380,1064000,50,5),
            (1,'6','งานสถาปัตย์','งานประตู-หน้าต่าง','ชุด',85,12000,1020000,30,6),
            (1,'7','งานระบบ MEP','งานไฟฟ้า','จุด',420,2500,1050000,20,7),
            (1,'8','งานระบบ MEP','งานประปา-สุขาภิบาล','จุด',180,3500,630000,15,8),
            (1,'9','งานตกแต่ง','งานพื้น-กระเบื้อง','ตร.ม.',3200,650,2080000,5,9),
            (1,'10','งานตกแต่ง','งานสีภายใน','ตร.ม.',5500,120,660000,0,10),
            (2,'1','งานโครงสร้าง','งานฐานราก-เสาเข็ม','ต้น',80,18000,1440000,80,1),
            (2,'2','งานโครงสร้าง','งานโครงสร้างเหล็ก','ตัน',45,65000,2925000,60,2),
            (2,'3','งานสถาปัตย์','งานผนัง Sandwich Panel','ตร.ม.',1800,850,1530000,40,3),
            (2,'4','งานระบบ MEP','งานไฟฟ้าโรงงาน','ชุด',1,850000,850000,20,4),
            (3,'1','งานถนน','งานดินขุด-ถม','ลบ.ม.',15000,180,2700000,100,1),
            (3,'2','งานถนน','งาน Sub-base','ตร.ม.',12000,280,3360000,95,2),
            (3,'3','งานถนน','งานลาดยาง Asphalt','ตร.ม.',12000,450,5400000,85,3),
            (3,'4','งานถนน','งานไหล่ทาง','ตร.ม.',4800,120,576000,70,4),
            (3,'5','งานถนน','งานเครื่องหมายจราจร','ตร.ม.',800,350,280000,10,5);
        """)
    db.commit()
    db.close()

# ══════════════════════════════════════════
#  CORS
# ══════════════════════════════════════════
@app.after_request
def add_cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

@app.route("/api/<path:p>", methods=["OPTIONS"])
def options_handler(p): return "", 204

# ══════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════
@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect("/")
    return send_from_directory("templates", "login.html")

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    d = request.get_json()
    username = (d.get("username") or "").strip().lower()
    password = d.get("password") or ""
    if not username or not password:
        return jsonify({"error": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"}), 400
    user = query("SELECT * FROM users WHERE username=? AND is_active=1", (username,), one=True)
    if not user or not verify_password(password, user["salt"], user["password_hash"]):
        return jsonify({"error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}), 401
    # Update last_login
    query("UPDATE users SET last_login=datetime('now','localtime') WHERE id=?", (user["id"],), commit=True)
    session["user_id"]      = user["id"]
    session["username"]     = user["username"]
    session["display_name"] = user["display_name"] or user["username"]
    session["role"]         = user["role"]
    session.permanent = True
    return jsonify({"message": "เข้าสู่ระบบสำเร็จ", "display_name": session["display_name"], "role": user["role"]})

@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "ออกจากระบบแล้ว"})

@app.route("/api/auth/me")
@login_required
def api_me():
    return jsonify({"username": session["username"], "display_name": session["display_name"], "role": session["role"]})

# ══════════════════════════════════════════
#  FRONTEND ROUTES
# ══════════════════════════════════════════

@app.route("/progress")
@login_required
def progress_page():
    return send_from_directory("templates", "progress.html")

@app.route("/")
@login_required
def index():
    return send_from_directory("templates", "index.html")

@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory("static", p)

# ══════════════════════════════════════════
#  API: DASHBOARD
# ══════════════════════════════════════════
@app.route("/api/dashboard")
@login_required
def dashboard():
    proj_count    = query("SELECT COUNT(*) as n FROM projects", one=True)["n"]
    worker_count  = query("SELECT COUNT(*) as n FROM workers", one=True)["n"]
    active_workers= query("SELECT COUNT(*) as n FROM workers WHERE status='เข้างาน'", one=True)["n"]
    delayed       = query("SELECT COUNT(*) as n FROM projects WHERE status='ล่าช้า'", one=True)["n"]
    income        = query("SELECT COALESCE(SUM(amount),0) as s FROM transactions WHERE type='income'", one=True)["s"]
    expense       = query("SELECT COALESCE(SUM(ABS(amount)),0) as s FROM transactions WHERE type='expense'", one=True)["s"]
    low_mat       = query("SELECT COUNT(*) as n FROM materials WHERE quantity <= min_quantity AND min_quantity > 0", one=True)["n"]
    recent_tx     = query("""SELECT t.*,p.name as project_name FROM transactions t
        LEFT JOIN projects p ON t.project_id=p.id ORDER BY t.created_at DESC LIMIT 5""")
    return jsonify({
        "project_count": proj_count, "worker_count": worker_count,
        "active_workers": active_workers, "delayed_projects": delayed,
        "total_income": income, "total_expense": expense,
        "net_profit": income - expense, "low_material_count": low_mat,
        "recent_transactions": recent_tx
    })

# ══════════════════════════════════════════
#  API: PROJECTS
# ══════════════════════════════════════════
@app.route("/api/projects", methods=["GET"])
@login_required
def get_projects():
    return jsonify(query("SELECT * FROM projects ORDER BY created_at DESC"))

@app.route("/api/projects/<int:pid>", methods=["GET"])
@login_required
def get_project(pid):
    row = query("SELECT * FROM projects WHERE id=?", (pid,), one=True)
    return jsonify(row) if row else (jsonify({"error": "not found"}), 404)

@app.route("/api/projects", methods=["POST"])
@login_required
def create_project():
    d = request.get_json()
    new_id = query("""INSERT INTO projects (name,client,project_type,location,value,start_date,end_date,status,note)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (d.get("name",""), d.get("client",""), d.get("project_type","อาคาร/คอนโด"),
         d.get("location",""), d.get("value",0), d.get("start_date",""),
         d.get("end_date",""), d.get("status","เริ่มต้น"), d.get("note","")), commit=True)
    return jsonify({"id": new_id, "message": "สร้างโครงการสำเร็จ"}), 201

@app.route("/api/projects/<int:pid>", methods=["PUT"])
@login_required
def update_project(pid):
    d = request.get_json()
    fields, vals = [], []
    for f in ["name","client","project_type","location","value","progress","start_date","end_date","status","note"]:
        if f in d: fields.append(f"{f}=?"); vals.append(d[f])
    if not fields: return jsonify({"error": "no fields"}), 400
    vals.append(pid)
    query(f"UPDATE projects SET {','.join(fields)} WHERE id=?", vals, commit=True)
    return jsonify({"message": "อัปเดตสำเร็จ"})

@app.route("/api/projects/<int:pid>", methods=["DELETE"])
@login_required
def delete_project(pid):
    query("DELETE FROM projects WHERE id=?", (pid,), commit=True)
    return jsonify({"message": "ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: WORKERS
# ══════════════════════════════════════════
@app.route("/api/workers", methods=["GET"])
@login_required
def get_workers():
    return jsonify(query("""SELECT w.*, p.name as project_name FROM workers w
        LEFT JOIN projects p ON w.project_id=p.id ORDER BY w.created_at DESC"""))

@app.route("/api/workers", methods=["POST"])
@login_required
def create_worker():
    d = request.get_json()
    new_id = query("INSERT INTO workers (name,role,project_id,wage,phone,id_card,status) VALUES (?,?,?,?,?,?,?)",
        (d.get("name",""), d.get("role",""), d.get("project_id"), d.get("wage",0),
         d.get("phone",""), d.get("id_card",""), d.get("status","เข้างาน")), commit=True)
    return jsonify({"id": new_id}), 201

@app.route("/api/workers/<int:wid>", methods=["PUT"])
@login_required
def update_worker(wid):
    d = request.get_json()
    fields, vals = [], []
    for f in ["name","role","project_id","wage","phone","id_card","status"]:
        if f in d: fields.append(f"{f}=?"); vals.append(d[f])
    vals.append(wid)
    query(f"UPDATE workers SET {','.join(fields)} WHERE id=?", vals, commit=True)
    return jsonify({"message": "อัปเดตสำเร็จ"})

@app.route("/api/workers/<int:wid>", methods=["DELETE"])
@login_required
def delete_worker(wid):
    query("DELETE FROM workers WHERE id=?", (wid,), commit=True)
    return jsonify({"message": "ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: MATERIALS
# ══════════════════════════════════════════
@app.route("/api/materials", methods=["GET"])
@login_required
def get_materials():
    return jsonify(query("SELECT * FROM materials ORDER BY name"))

@app.route("/api/materials", methods=["POST"])
@login_required
def create_material():
    d = request.get_json()
    new_id = query("INSERT INTO materials (name,unit,quantity,min_quantity,price_per_unit,supplier) VALUES (?,?,?,?,?,?)",
        (d.get("name",""), d.get("unit","หน่วย"), d.get("quantity",0),
         d.get("min_quantity",0), d.get("price_per_unit",0), d.get("supplier","")), commit=True)
    return jsonify({"id": new_id}), 201

@app.route("/api/materials/<int:mid>", methods=["PUT"])
@login_required
def update_material(mid):
    d = request.get_json()
    fields, vals = [], []
    for f in ["name","unit","quantity","min_quantity","price_per_unit","supplier"]:
        if f in d: fields.append(f"{f}=?"); vals.append(d[f])
    vals.append(mid)
    query(f"UPDATE materials SET {','.join(fields)} WHERE id=?", vals, commit=True)
    return jsonify({"message": "อัปเดตสำเร็จ"})

@app.route("/api/materials/<int:mid>", methods=["DELETE"])
@login_required
def delete_material(mid):
    query("DELETE FROM materials WHERE id=?", (mid,), commit=True)
    return jsonify({"message": "ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: EQUIPMENT
# ══════════════════════════════════════════
@app.route("/api/equipment", methods=["GET"])
@login_required
def get_equipment():
    return jsonify(query("""SELECT e.*, p.name as project_name FROM equipment e
        LEFT JOIN projects p ON e.project_id=p.id ORDER BY e.name"""))

@app.route("/api/equipment", methods=["POST"])
@login_required
def create_equipment():
    d = request.get_json()
    new_id = query("INSERT INTO equipment (name,serial_no,project_id,status,note) VALUES (?,?,?,?,?)",
        (d.get("name",""), d.get("serial_no",""), d.get("project_id"),
         d.get("status","ว่าง"), d.get("note","")), commit=True)
    return jsonify({"id": new_id}), 201

@app.route("/api/equipment/<int:eid>", methods=["PUT"])
@login_required
def update_equipment(eid):
    d = request.get_json()
    fields, vals = [], []
    for f in ["name","serial_no","project_id","status","note"]:
        if f in d: fields.append(f"{f}=?"); vals.append(d[f])
    vals.append(eid)
    query(f"UPDATE equipment SET {','.join(fields)} WHERE id=?", vals, commit=True)
    return jsonify({"message": "อัปเดตสำเร็จ"})

@app.route("/api/equipment/<int:eid>", methods=["DELETE"])
@login_required
def delete_equipment(eid):
    query("DELETE FROM equipment WHERE id=?", (eid,), commit=True)
    return jsonify({"message": "ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: TRANSACTIONS
# ══════════════════════════════════════════
@app.route("/api/transactions", methods=["GET"])
@login_required
def get_transactions():
    return jsonify(query("""SELECT t.*, p.name as project_name FROM transactions t
        LEFT JOIN projects p ON t.project_id=p.id ORDER BY t.tx_date DESC, t.created_at DESC"""))

@app.route("/api/transactions", methods=["POST"])
@login_required
def create_transaction():
    d = request.get_json()
    amount = float(d.get("amount", 0))
    if d.get("type") == "expense" and amount > 0: amount = -amount
    new_id = query("INSERT INTO transactions (project_id,type,category,description,amount,tx_date) VALUES (?,?,?,?,?,?)",
        (d.get("project_id"), d.get("type","income"), d.get("category",""),
         d.get("description",""), amount,
         d.get("tx_date", str(datetime.date.today()))), commit=True)
    return jsonify({"id": new_id}), 201

@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
@login_required
def delete_transaction(tid):
    query("DELETE FROM transactions WHERE id=?", (tid,), commit=True)
    return jsonify({"message": "ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: SAFETY
# ══════════════════════════════════════════
@app.route("/api/safety", methods=["GET"])
@login_required
def get_safety():
    return jsonify(query("""SELECT s.*, p.name as project_name FROM safety_incidents s
        LEFT JOIN projects p ON s.project_id=p.id ORDER BY s.inc_date DESC"""))

@app.route("/api/safety", methods=["POST"])
@login_required
def create_safety():
    d = request.get_json()
    new_id = query("INSERT INTO safety_incidents (project_id,description,severity,inc_date) VALUES (?,?,?,?)",
        (d.get("project_id"), d.get("description",""), d.get("severity","เล็กน้อย"),
         d.get("inc_date", str(datetime.date.today()))), commit=True)
    return jsonify({"id": new_id}), 201


# ══════════════════════════════════════════
#  SERVE UPLOADED IMAGES
# ══════════════════════════════════════════
@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/health")
def health():
    """Health check endpoint for Render"""
    return {"status":"ok","service":"BuildMaster Pro"}

# ══════════════════════════════════════════
#  API: BOQ ITEMS
# ══════════════════════════════════════════
@app.route("/api/boq/<int:pid>", methods=["GET"])
@login_required
def get_boq(pid):
    rows = query("SELECT * FROM boq_items WHERE project_id=? ORDER BY sort_order,id", (pid,))
    return jsonify(rows)

@app.route("/api/boq/<int:pid>", methods=["POST"])
@login_required
def create_boq_item(pid):
    d = request.get_json()
    qty   = float(d.get("quantity", 1))
    price = float(d.get("unit_price", 0))
    new_id = query("""INSERT INTO boq_items
        (project_id,item_no,category,description,unit,quantity,unit_price,total_price,progress_pct,sort_order)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (pid, d.get("item_no",""), d.get("category",""), d.get("description",""),
         d.get("unit","งาน"), qty, price, qty*price,
         d.get("progress_pct",0), d.get("sort_order",999)), commit=True)
    return jsonify({"id": new_id}), 201

@app.route("/api/boq/item/<int:bid>", methods=["PUT"])
@login_required
def update_boq_item(bid):
    d = request.get_json()
    fields, vals = [], []
    for f in ["item_no","category","description","unit","quantity","unit_price","total_price","progress_pct","sort_order"]:
        if f in d: fields.append(f"{f}=?"); vals.append(d[f])
    if not fields: return jsonify({"error":"no fields"}), 400
    vals.append(bid)
    query(f"UPDATE boq_items SET {','.join(fields)} WHERE id=?", vals, commit=True)
    return jsonify({"message":"อัปเดตสำเร็จ"})

@app.route("/api/boq/item/<int:bid>", methods=["DELETE"])
@login_required
def delete_boq_item(bid):
    query("DELETE FROM boq_items WHERE id=?", (bid,), commit=True)
    return jsonify({"message":"ลบสำเร็จ"})

# ══════════════════════════════════════════
#  API: PROGRESS REPORTS
# ══════════════════════════════════════════
@app.route("/api/reports/<int:pid>", methods=["GET"])
@login_required
def get_reports(pid):
    rows = query("""
        SELECT r.*,
               u.display_name as reporter_name,
               rv.display_name as reviewer_name,
               b.description as boq_description,
               b.category as boq_category,
               b.item_no as boq_item_no,
               (SELECT COUNT(*) FROM report_photos WHERE report_id=r.id) as photo_count
        FROM progress_reports r
        LEFT JOIN users u  ON r.reported_by=u.id
        LEFT JOIN users rv ON r.reviewed_by=rv.id
        LEFT JOIN boq_items b ON r.boq_item_id=b.id
        WHERE r.project_id=?
        ORDER BY r.report_date DESC, r.created_at DESC
    """, (pid,))
    return jsonify(rows)

@app.route("/api/reports/detail/<int:rid>", methods=["GET"])
@login_required
def get_report_detail(rid):
    report = query("""
        SELECT r.*,
               u.display_name as reporter_name,
               rv.display_name as reviewer_name,
               b.description as boq_description,
               b.category as boq_category,
               b.item_no as boq_item_no,
               p.name as project_name
        FROM progress_reports r
        LEFT JOIN users u  ON r.reported_by=u.id
        LEFT JOIN users rv ON r.reviewed_by=rv.id
        LEFT JOIN boq_items b ON r.boq_item_id=b.id
        LEFT JOIN projects p ON r.project_id=p.id
        WHERE r.id=?
    """, (rid,), one=True)
    if not report: return jsonify({"error":"not found"}), 404
    photos = query("SELECT * FROM report_photos WHERE report_id=? ORDER BY sort_order", (rid,))
    report["photos"] = photos
    return jsonify(report)

@app.route("/api/reports/<int:pid>", methods=["POST"])
@login_required
def create_report(pid):
    # Multipart form with photos
    title        = request.form.get("title","").strip()
    description  = request.form.get("description","")
    boq_item_id  = request.form.get("boq_item_id") or None
    progress_pct = int(request.form.get("progress_pct", 0))
    weather      = request.form.get("weather","แจ่มใส")
    workers_count= int(request.form.get("workers_count", 0))
    report_date  = request.form.get("report_date", str(datetime.date.today()))

    if not title:
        return jsonify({"error":"กรุณากรอกหัวข้อรายงาน"}), 400

    photos = request.files.getlist("photos")
    if len(photos) < 3:
        return jsonify({"error":"กรุณาอัปโหลดรูปภาพอย่างน้อย 3 ภาพ"}), 400

    # Validate file types
    allowed = {"image/jpeg","image/png","image/webp","image/heic","image/heif"}
    for f in photos:
        mt = f.content_type or mimetypes.guess_type(f.filename)[0] or ""
        if mt.lower() not in allowed:
            return jsonify({"error":f"ไฟล์ {f.filename} ไม่ใช่รูปภาพ (jpg/png/webp)"}), 400

    # Create report
    new_id = query("""INSERT INTO progress_reports
        (project_id,boq_item_id,reported_by,report_date,title,description,
         progress_pct,weather,workers_count,status)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (pid, boq_item_id, session["user_id"], report_date, title, description,
         progress_pct, weather, workers_count, "รอตรวจสอบ"), commit=True)

    # Save photos
    import uuid
    for i, photo in enumerate(photos):
        ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
        fname = f"report_{new_id}_{uuid.uuid4().hex[:8]}{ext}"
        photo.save(os.path.join(UPLOAD_FOLDER, fname))
        caption = request.form.get(f"caption_{i}", "")
        query("INSERT INTO report_photos (report_id,filename,caption,sort_order) VALUES (?,?,?,?)",
              (new_id, fname, caption, i), commit=True)

    # Update boq item progress if provided
    if boq_item_id:
        query("UPDATE boq_items SET progress_pct=? WHERE id=?",
              (progress_pct, boq_item_id), commit=True)
        # Recalculate project overall progress
        avg = query("""SELECT AVG(progress_pct) as avg FROM boq_items
                       WHERE project_id=?""", (pid,), one=True)
        if avg and avg["avg"] is not None:
            query("UPDATE projects SET progress=? WHERE id=?",
                  (int(avg["avg"]), pid), commit=True)

    return jsonify({"id": new_id, "message":"บันทึกรายงานสำเร็จ"}), 201

@app.route("/api/reports/review/<int:rid>", methods=["PUT"])
@login_required
def review_report(rid):
    d = request.get_json()
    query("""UPDATE progress_reports
             SET status=?, reviewer_note=?, reviewed_by=?,
                 reviewed_at=datetime('now','localtime')
             WHERE id=?""",
          (d.get("status","อนุมัติ"), d.get("reviewer_note",""),
           session["user_id"], rid), commit=True)
    return jsonify({"message":"บันทึกการตรวจสอบสำเร็จ"})

@app.route("/api/reports/detail/<int:rid>", methods=["DELETE"])
@login_required
def delete_report(rid):
    # Delete photos from disk
    photos = query("SELECT filename FROM report_photos WHERE report_id=?", (rid,))
    for p in photos:
        fpath = os.path.join(UPLOAD_FOLDER, p["filename"])
        if os.path.exists(fpath): os.remove(fpath)
    query("DELETE FROM progress_reports WHERE id=?", (rid,), commit=True)
    return jsonify({"message":"ลบรายงานสำเร็จ"})

# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("  BuildMaster Pro — Server Starting")
    print("  เปิดเบราว์เซอร์: http://localhost:5000")
    print("")
    print("  ⚠️  ยังไม่มีผู้ใช้? สร้างด้วยคำสั่ง:")
    print("  python manage.py create-user")
    print("=" * 55)
    app.run(debug=False, port=5000, host="0.0.0.0")
