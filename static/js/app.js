/* ════════════════════════════════════════
   BuildMaster Pro — Main App Logic
   ════════════════════════════════════════ */

let currentTab = "home";
let allProjects = [];
let allWorkers  = [];
let currentFilter = { projects: "all", workers: "all" };

// ══════════════════════════════════════════
//  NAVIGATION
// ══════════════════════════════════════════
function switchTab(tab) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  const page = document.getElementById("pg-" + tab);
  const nav  = document.getElementById("nav-" + tab);
  if (page) page.classList.add("active");
  if (nav)  nav.classList.add("active");
  const fab = document.getElementById("fab");
  fab.style.display = ["projects", "workers"].includes(tab) ? "flex" : "none";
  currentTab = tab;
  loadTab(tab);
}

function loadTab(tab) {
  if (tab === "home")     loadHome();
  if (tab === "projects") loadProjects();
  if (tab === "workers")  loadWorkers();
  if (tab === "finance")  loadFinance();
  if (tab === "more")     loadMore();
}

// ══════════════════════════════════════════
//  HOME
// ══════════════════════════════════════════
async function loadHome() {
  try {
    const d = await getDashboard();
    document.getElementById("stat-projects").textContent = d.project_count;
    document.getElementById("stat-income").textContent   = fmtMoney(d.total_income);
    document.getElementById("stat-workers").textContent  = d.active_workers;
    document.getElementById("stat-delayed").textContent  = d.delayed_projects;
    if (d.low_material_count > 0) {
      const b = document.getElementById("low-mat-banner");
      b.style.display = "flex";
      b.textContent = "⚠️ วัสดุ " + d.low_material_count + " รายการใกล้หมด — กรุณาตรวจสอบ";
    }
    // Recent transactions
    const txList = document.getElementById("home-transactions");
    txList.innerHTML = d.recent_transactions.length
      ? d.recent_transactions.map(renderTransactionItem).join("")
      : emptyState("💰", "ยังไม่มีรายการเงิน");
  } catch (e) { console.error(e); }

  // Projects (mini)
  try {
    const projects = await getProjects();
    const hp = document.getElementById("home-projects");
    const active = projects.filter(p => p.status !== "เสร็จแล้ว").slice(0, 3);
    hp.innerHTML = active.length
      ? active.map(p => renderProjectCard(p, true)).join("")
      : emptyState("🏢", "ยังไม่มีโครงการ");
  } catch(e) {}
}

// ══════════════════════════════════════════
//  PROJECTS
// ══════════════════════════════════════════
async function loadProjects() {
  const list = document.getElementById("project-list");
  list.innerHTML = `<div class="loading-shimmer"></div><div class="loading-shimmer" style="height:60px;margin-top:0"></div>`;
  try {
    allProjects = await getProjects();
    document.getElementById("proj-count-label").textContent = `${allProjects.length} โครงการ`;
    renderFilteredProjects();
  } catch(e) {
    list.innerHTML = emptyState("❌", "โหลดข้อมูลไม่สำเร็จ");
  }
}

function renderFilteredProjects() {
  const list = document.getElementById("project-list");
  const f = currentFilter.projects;
  const filtered = f === "all" ? allProjects : allProjects.filter(p => p.status === f);
  list.innerHTML = filtered.length
    ? filtered.map(p => renderProjectCard(p)).join("")
    : emptyState("🏢", "ไม่พบโครงการ");
}

function filterProjects(status, el) {
  currentFilter.projects = status;
  document.querySelectorAll("#proj-filter .filter-chip").forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  renderFilteredProjects();
}

async function openEditProject(id) {
  try {
    const p = await getProject(id);
    document.getElementById("ep-id").value      = p.id;
    document.getElementById("ep-name").value    = p.name;
    document.getElementById("ep-client").value  = p.client;
    document.getElementById("ep-progress").value= p.progress;
    document.getElementById("ep-value").value   = p.value;
    document.getElementById("ep-start").value   = p.start_date || "";
    document.getElementById("ep-end").value     = p.end_date   || "";
    const sel = document.getElementById("ep-status");
    for (let o of sel.options) if (o.value === p.status) o.selected = true;
    openSheet("editProjectSheet");
  } catch(e) {}
}

async function updateProject() {
  const id = document.getElementById("ep-id").value;
  const data = {
    name:       document.getElementById("ep-name").value.trim(),
    client:     document.getElementById("ep-client").value.trim(),
    progress:   parseInt(document.getElementById("ep-progress").value) || 0,
    value:      parseFloat(document.getElementById("ep-value").value) || 0,
    start_date: document.getElementById("ep-start").value,
    end_date:   document.getElementById("ep-end").value,
    status:     document.getElementById("ep-status").value,
  };
  if (!data.name) { showToast("⚠️ กรุณากรอกชื่อโครงการ"); return; }
  try {
    await updateProject_(id, data);
    closeSheet("editProjectSheet");
    showToast("✅ อัปเดตโครงการสำเร็จ");
    loadProjects(); loadHome();
  } catch(e) {}
}

async function doDeleteProject(id) {
  try {
    await deleteProject_(id);
    showToast("🗑 ลบโครงการสำเร็จ");
    loadProjects(); loadHome();
  } catch(e) {}
}

async function submitProject() {
  const data = {
    name:         document.getElementById("p-name").value.trim(),
    client:       document.getElementById("p-client").value.trim(),
    project_type: document.getElementById("p-type").value,
    value:        parseFloat(document.getElementById("p-value").value) || 0,
    location:     document.getElementById("p-loc").value.trim(),
    start_date:   document.getElementById("p-start").value,
    end_date:     document.getElementById("p-end").value,
    note:         document.getElementById("p-note").value.trim(),
    status:       "เริ่มต้น",
  };
  if (!data.name || !data.client) { showToast("⚠️ กรุณากรอกชื่อโครงการและลูกค้า"); return; }
  try {
    await createProject(data);
    closeSheet("addProjectSheet");
    showToast("✅ สร้างโครงการ "" + data.name + "" สำเร็จ");
    ["p-name","p-client","p-value","p-loc","p-start","p-end","p-note"].forEach(id => document.getElementById(id).value = "");
    loadProjects(); loadHome();
  } catch(e) {}
}

// ══════════════════════════════════════════
//  WORKERS
// ══════════════════════════════════════════
async function loadWorkers() {
  const list = document.getElementById("worker-list");
  list.innerHTML = `<div class="loading-shimmer"></div>`;
  try {
    allWorkers = await getWorkers();
    document.getElementById("worker-count-label").textContent =
      `${allWorkers.length} คน • เข้างาน ${allWorkers.filter(w=>w.status==="เข้างาน").length} คน`;
    renderFilteredWorkers();
    populateProjectDropdowns();
  } catch(e) {
    list.innerHTML = emptyState("❌", "โหลดข้อมูลไม่สำเร็จ");
  }
}

function renderFilteredWorkers() {
  const list = document.getElementById("worker-list");
  const f = currentFilter.workers;
  const filtered = f === "all" ? allWorkers : allWorkers.filter(w => w.status === f);
  list.innerHTML = filtered.length
    ? filtered.map(renderWorkerCard).join("")
    : emptyState("👷", "ไม่พบพนักงาน");
}

function filterWorkers(status, el) {
  currentFilter.workers = status;
  document.querySelectorAll("#pg-workers .filter-chip").forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  renderFilteredWorkers();
}

async function submitWorker() {
  const fname = document.getElementById("w-name").value.trim();
  const lname = document.getElementById("w-lname").value.trim();
  const name = fname + (lname ? " " + lname : "");
  if (!fname) { showToast("⚠️ กรุณากรอกชื่อ"); return; }
  const projSel = document.getElementById("w-project");
  const project_id = projSel.value ? parseInt(projSel.value) : null;
  const data = {
    name, role: document.getElementById("w-role").value,
    project_id, wage: parseFloat(document.getElementById("w-wage").value) || 0,
    phone: document.getElementById("w-phone").value.trim(),
    id_card: document.getElementById("w-id").value.trim(),
    status: "เข้างาน",
  };
  try {
    await createWorker(data);
    closeSheet("addWorkerSheet");
    showToast("✅ เพิ่มพนักงาน "" + name + "" สำเร็จ");
    ["w-name","w-lname","w-wage","w-phone","w-id"].forEach(id => document.getElementById(id).value = "");
    loadWorkers();
  } catch(e) {}
}

// ══════════════════════════════════════════
//  FINANCE
// ══════════════════════════════════════════
async function loadFinance() {
  try {
    const [dash, txs] = await Promise.all([getDashboard(), getTransactions()]);
    document.getElementById("fin-income").textContent  = "+฿" + fmtMoney(dash.total_income);
    document.getElementById("fin-expense").textContent = "-฿" + fmtMoney(dash.total_expense);
    const profit = dash.net_profit;
    const el = document.getElementById("fin-profit");
    el.textContent = (profit >= 0 ? "+" : "") + "฿" + fmtMoney(profit);
    el.className = "fin-sum-value " + (profit >= 0 ? "green" : "red");
    document.getElementById("transaction-list").innerHTML = txs.length
      ? txs.map(renderTransactionItem).join("")
      : emptyState("💰", "ยังไม่มีรายการ");
  } catch(e) {}
}

async function submitTransaction() {
  const type = document.querySelector("input[name='tx-type']:checked").value;
  const amount = parseFloat(document.getElementById("tx-amount").value);
  if (!document.getElementById("tx-desc").value.trim() || !amount) {
    showToast("⚠️ กรุณากรอกรายละเอียดและจำนวนเงิน"); return;
  }
  const projSel = document.getElementById("tx-project");
  const data = {
    type, amount,
    description: document.getElementById("tx-desc").value.trim(),
    category:    document.getElementById("tx-cat").value,
    project_id:  projSel.value ? parseInt(projSel.value) : null,
    tx_date:     document.getElementById("tx-date").value || new Date().toISOString().split("T")[0],
  };
  try {
    await createTransaction(data);
    closeSheet("addTransSheet");
    showToast("✅ บันทึกรายการสำเร็จ");
    ["tx-desc","tx-amount","tx-date"].forEach(id => document.getElementById(id).value = "");
    loadFinance();
  } catch(e) {}
}

// ══════════════════════════════════════════
//  MORE (Materials, Equipment, Safety)
// ══════════════════════════════════════════
async function loadMore() {
  try {
    const [mats, equip, safety] = await Promise.all([getMaterials(), getEquipment(), getSafety()]);

    // Materials
    const matList = document.getElementById("material-list");
    if (mats.length) {
      const low = mats.filter(m => m.quantity <= m.min_quantity);
      const banner = low.length
        ? `<div class="alert-banner alert-danger" style="margin-bottom:0">⚠️ วัสดุ ${low.length} รายการต่ำกว่าขั้นต่ำ</div>`
        : "";
      matList.innerHTML = banner + mats.map(renderMaterialCard).join("");
    } else {
      matList.innerHTML = emptyState("🧱", "ยังไม่มีวัสดุในคลัง");
    }

    // Equipment
    document.getElementById("equipment-list").innerHTML = equip.length
      ? equip.map(renderEquipmentItem).join("")
      : emptyState("🚜", "ยังไม่มีเครื่องจักร");

    // Safety
    document.getElementById("safety-list").innerHTML = safety.length
      ? safety.map(renderSafetyItem).join("")
      : emptyState("⛑️", "ไม่มีรายงานอุบัติเหตุ 🎉");
  } catch(e) {}
}

async function submitMaterial() {
  const name = document.getElementById("m-name").value.trim();
  if (!name) { showToast("⚠️ กรุณากรอกชื่อวัสดุ"); return; }
  const data = {
    name, unit: document.getElementById("m-unit").value,
    quantity:       parseFloat(document.getElementById("m-qty").value)   || 0,
    price_per_unit: parseFloat(document.getElementById("m-price").value) || 0,
    min_quantity:   parseFloat(document.getElementById("m-min").value)   || 0,
    supplier:       document.getElementById("m-supplier").value.trim(),
  };
  try {
    await createMaterial(data);
    closeSheet("addMaterialSheet");
    showToast("✅ เพิ่มวัสดุสำเร็จ");
    ["m-name","m-qty","m-price","m-min","m-supplier"].forEach(id => document.getElementById(id).value = "");
    loadMore();
  } catch(e) {}
}

async function submitEquipment() {
  const name = document.getElementById("eq-name").value.trim();
  if (!name) { showToast("⚠️ กรุณากรอกชื่อเครื่องจักร"); return; }
  const projSel = document.getElementById("eq-project");
  const data = {
    name, serial_no: document.getElementById("eq-serial").value.trim(),
    status: document.getElementById("eq-status").value,
    project_id: projSel.value ? parseInt(projSel.value) : null,
  };
  try {
    await createEquipment(data);
    closeSheet("addEquipSheet");
    showToast("✅ เพิ่มเครื่องจักรสำเร็จ");
    ["eq-name","eq-serial"].forEach(id => document.getElementById(id).value = "");
    loadMore();
  } catch(e) {}
}

async function submitSafety() {
  const desc = document.getElementById("sf-desc").value.trim();
  if (!desc) { showToast("⚠️ กรุณากรอกรายละเอียด"); return; }
  const projSel = document.getElementById("sf-project");
  const data = {
    description: desc,
    severity:    document.getElementById("sf-sev").value,
    inc_date:    document.getElementById("sf-date").value || new Date().toISOString().split("T")[0],
    project_id:  projSel.value ? parseInt(projSel.value) : null,
  };
  try {
    await createSafety(data);
    closeSheet("addSafetySheet");
    showToast("✅ บันทึกรายงานสำเร็จ");
    document.getElementById("sf-desc").value = "";
    loadMore();
  } catch(e) {}
}

// ══════════════════════════════════════════
//  FAB
// ══════════════════════════════════════════
function fabAction() {
  if (currentTab === "projects") openSheet("addProjectSheet");
  else if (currentTab === "workers") openSheet("addWorkerSheet");
}

// ══════════════════════════════════════════
//  SHEETS
// ══════════════════════════════════════════
function openSheet(id) { document.getElementById(id).classList.add("open"); }
function closeSheet(id, e) {
  if (e && e.target !== document.getElementById(id)) return;
  document.getElementById(id).classList.remove("open");
}

// ══════════════════════════════════════════
//  CONFIRM DIALOG
// ══════════════════════════════════════════
function confirmDelete(name, fn) {
  document.getElementById("confirm-body").textContent = "คุณต้องการลบ "" + name + "" ใช่หรือไม่? การกระทำนี้ไม่สามารถยกเลิกได้";
  const btn = document.getElementById("confirm-ok");
  btn.onclick = () => { closeSheet("confirmDialog"); fn(); };
  openSheet("confirmDialog");
}

// ══════════════════════════════════════════
//  TOAST
// ══════════════════════════════════════════
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2800);
}

// ══════════════════════════════════════════
//  POPULATE PROJECT DROPDOWNS
// ══════════════════════════════════════════
async function populateProjectDropdowns() {
  const projects = allProjects.length ? allProjects : await getProjects();
  const opts = `<option value="">— ไม่ระบุ —</option>` +
    projects.map(p => `<option value="${p.id}">${p.name}</option>`).join("");
  ["w-project","tx-project","eq-project","sf-project"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts;
  });
}

// ══════════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════════
function handleSearch(q) {
  if (!q) { renderFilteredProjects(); return; }
  q = q.toLowerCase();
  if (currentTab === "projects") {
    const filtered = allProjects.filter(p =>
      p.name.toLowerCase().includes(q) || p.client.toLowerCase().includes(q) || (p.location||"").toLowerCase().includes(q)
    );
    document.getElementById("project-list").innerHTML = filtered.length
      ? filtered.map(p => renderProjectCard(p)).join("")
      : emptyState("🔍", `ไม่พบผลลัพธ์สำหรับ "${q}"`);
  }
}

// ══════════════════════════════════════════
//  CLOCK
// ══════════════════════════════════════════
function updateClock() {
  const now = new Date();
  const h = now.getHours().toString().padStart(2,"0");
  const m = now.getMinutes().toString().padStart(2,"0");
  document.getElementById("clock").textContent = h + ":" + m;
}

// ══════════════════════════════════════════
//  GREETING
// ══════════════════════════════════════════
function setGreeting() {
  const h = new Date().getHours();
  const greet = h < 12 ? "สวัสดีตอนเช้า" : h < 17 ? "สวัสดีตอนบ่าย" : "สวัสดีตอนเย็น";
  document.getElementById("greeting").textContent = greet + ", สมชาย";
}

// ══════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {
  updateClock();
  setInterval(updateClock, 15000);
  setGreeting();

  // Set today's date on date inputs
  const today = new Date().toISOString().split("T")[0];
  ["tx-date","sf-date"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });

  // Init home
  await loadHome();

  // Preload projects for dropdowns
  try {
    allProjects = await getProjects();
    populateProjectDropdowns();
  } catch(e) {}
});
