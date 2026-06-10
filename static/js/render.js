/* ════════════════════════════════════════
   BuildMaster Pro — Render Functions
   ════════════════════════════════════════ */

// ── HELPERS ──
function fmtMoney(n) {
  n = Math.abs(Number(n));
  if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (n >= 1000)    return (n / 1000).toFixed(0) + "K";
  return n.toLocaleString("th-TH");
}

function statusColor(s) {
  const map = {
    "กำลังก่อสร้าง": ["var(--amber)", "pill-amber"],
    "ตามแผน":        ["var(--green)", "pill-green"],
    "ล่าช้า":         ["var(--red)",   "pill-red"],
    "เริ่มต้น":       ["var(--blue)",  "pill-blue"],
    "เกือบเสร็จ":    ["var(--green)", "pill-green"],
    "เสร็จแล้ว":     ["#8b949e",      "pill-gray"],
    "เพิ่งสร้าง":    ["var(--blue)",  "pill-blue"],
  };
  return map[s] || ["var(--muted)", "pill-gray"];
}

function workerStatusPill(s) {
  const map = { "เข้างาน": "pill-green", "ลาป่วย": "pill-red", "ลากิจ": "pill-amber", "OT": "pill-amber", "ขาดงาน": "pill-red" };
  return map[s] || "pill-gray";
}

function avatarColor(name) {
  const colors = ["#3b82f6","#f59e0b","#10b981","#8b5cf6","#ef4444","#06b6d4","#f97316","#ec4899"];
  let h = 0;
  for (let c of (name || "?")) h = (h * 31 + c.charCodeAt(0)) & 0xffffffff;
  return colors[Math.abs(h) % colors.length];
}

function equip_status_pill(s) {
  const map = { "ว่าง": "pill-blue", "ใช้งาน": "pill-green", "ซ่อมบำรุง": "pill-amber", "เสีย": "pill-red" };
  return map[s] || "pill-gray";
}

function safety_pill(s) {
  const map = { "Near Miss": "pill-gray", "เล็กน้อย": "pill-amber", "ปานกลาง": "pill-amber", "รุนแรง": "pill-red" };
  return map[s] || "pill-gray";
}

function matPct(qty, min) {
  if (!min || min === 0) return 100;
  return Math.min(100, Math.round((qty / (min * 3)) * 100));
}

function matStatusPill(qty, min) {
  if (qty <= min * 0.3) return ["pill-red", "วิกฤต", "var(--red)"];
  if (qty <= min)       return ["pill-amber", "ต่ำ", "var(--amber)"];
  return ["pill-green", "ปกติ", "var(--green)"];
}

// ── PROJECTS ──
function renderProjectCard(p, mini = false) {
  const [color, pillClass] = statusColor(p.status);
  const pct = p.progress || 0;
  return `
    <div class="project-card" data-id="${p.id}">
      <div class="project-stripe" style="background:${color}"></div>
      <div class="project-card-inner">
        <div class="proj-name">${p.name}</div>
        <div class="proj-client">${p.client}</div>
        <div class="proj-value">฿ ${Number(p.value).toLocaleString("th-TH")}</div>
        <div class="proj-footer">
          <div>
            <div class="proj-pct" style="color:${color}">${pct}%</div>
            <div class="prog-bar">
              <div class="prog-fill" style="width:${pct}%;background:${color}"></div>
            </div>
            ${p.end_date ? `<div style="font-size:.7rem;color:var(--muted);margin-top:4px">ส่ง ${p.end_date}</div>` : ""}
          </div>
          <div class="proj-meta">
            <span class="pill ${pillClass}">${p.status}</span>
          </div>
        </div>
        ${!mini ? `
        <div class="proj-actions">
          <button class="btn btn-sm btn-edit-sm" onclick="openEditProject(${p.id})">✏️ แก้ไข</button>
          <button class="btn btn-sm btn-danger-sm" onclick="confirmDelete('โครงการ: ${p.name}', () => doDeleteProject(${p.id}))">🗑 ลบ</button>
        </div>` : ""}
      </div>
    </div>`;
}

// ── WORKERS ──
function renderWorkerCard(w) {
  const col = avatarColor(w.name);
  const pillClass = workerStatusPill(w.status);
  return `
    <div class="worker-card" data-id="${w.id}">
      <div class="w-avatar" style="background:linear-gradient(135deg,${col},${col}99)">
        ${(w.name || "?")[0]}
      </div>
      <div style="flex:1;min-width:0">
        <div class="w-name">${w.name}</div>
        <div class="w-role">${w.role}${w.project_name ? " • " + w.project_name : ""}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div class="w-wage">฿${Number(w.wage).toLocaleString()}/วัน</div>
        <span class="pill ${pillClass}" style="margin-top:4px;display:inline-block">${w.status}</span>
      </div>
    </div>`;
}

// ── MATERIALS ──
function renderMaterialCard(m) {
  const pct = matPct(m.quantity, m.min_quantity);
  const [pillClass, statusText, barColor] = matStatusPill(m.quantity, m.min_quantity);
  const total = (m.quantity * m.price_per_unit).toLocaleString("th-TH");
  return `
    <div class="mat-card" data-id="${m.id}">
      <div class="mat-header">
        <div>
          <div class="mat-name">${m.name}</div>
          <div class="mat-unit">${m.unit}${m.supplier ? " • " + m.supplier : ""}</div>
        </div>
        <div style="text-align:right">
          <div class="mat-stock" style="color:${barColor}">${Number(m.quantity).toLocaleString()}</div>
          <span class="pill ${pillClass}">${statusText}</span>
        </div>
      </div>
      <div class="mat-bar">
        <div class="mat-fill" style="width:${pct}%;background:${barColor}"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.75rem;color:var(--muted)">
        <span>ขั้นต่ำ: ${m.min_quantity} ${m.unit}</span>
        <span>มูลค่า: ฿ ${total}</span>
      </div>
    </div>`;
}

// ── EQUIPMENT ──
function renderEquipmentItem(e) {
  const pillClass = equip_status_pill(e.status);
  const icons = { "ว่าง": "⚙️", "ใช้งาน": "🚜", "ซ่อมบำรุง": "🔧", "เสีย": "🔴" };
  const icon = icons[e.status] || "🚜";
  return `
    <div class="list-item" data-id="${e.id}">
      <div class="list-icon gray">${icon}</div>
      <div class="list-body">
        <div class="list-title">${e.name}</div>
        <div class="list-sub">${e.serial_no || "—"}${e.project_name ? " • " + e.project_name : ""}</div>
      </div>
      <span class="pill ${pillClass}">${e.status}</span>
    </div>`;
}

// ── TRANSACTIONS ──
function renderTransactionItem(t) {
  const isIncome = t.type === "income";
  const color = isIncome ? "var(--green)" : "var(--red)";
  const sign  = isIncome ? "+" : "-";
  const icon  = isIncome ? "💵" : "💸";
  const iconClass = isIncome ? "green" : "red";
  return `
    <div class="list-item" data-id="${t.id}">
      <div class="list-icon ${iconClass}">${icon}</div>
      <div class="list-body">
        <div class="list-title">${t.description}</div>
        <div class="list-sub">${t.project_name || "—"} • ${t.category || ""}</div>
      </div>
      <div class="list-right">
        <div class="list-amount" style="color:${color}">${sign}฿${fmtMoney(t.amount)}</div>
        <div class="list-time">${t.tx_date || ""}</div>
      </div>
    </div>`;
}

// ── SAFETY ──
function renderSafetyItem(s) {
  const pillClass = safety_pill(s.severity);
  return `
    <div class="list-item" data-id="${s.id}">
      <div class="list-icon red">⛑️</div>
      <div class="list-body">
        <div class="list-title">${s.description}</div>
        <div class="list-sub">${s.project_name || "—"} • ${s.inc_date || ""}</div>
      </div>
      <span class="pill ${pillClass}">${s.severity}</span>
    </div>`;
}

// ── EMPTY STATE ──
function emptyState(icon, text) {
  return `<div class="empty-state"><span class="empty-icon">${icon}</span><div class="empty-text">${text}</div></div>`;
}
