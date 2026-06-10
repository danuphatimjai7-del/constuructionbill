/* ════════════════════════════════════════
   BuildMaster Pro — API Client
   ════════════════════════════════════════ */

const API = ""; // same origin

async function apiFetch(path, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(API + path, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "เกิดข้อผิดพลาด");
    return data;
  } catch (e) {
    showToast("❌ " + e.message);
    throw e;
  }
}

// Dashboard
const getDashboard = () => apiFetch("/api/dashboard");

// Projects
const getProjects   = () => apiFetch("/api/projects");
const getProject    = (id) => apiFetch(`/api/projects/${id}`);
const createProject = (d) => apiFetch("/api/projects", "POST", d);
const updateProject_ = (id, d) => apiFetch(`/api/projects/${id}`, "PUT", d);
const deleteProject_ = (id) => apiFetch(`/api/projects/${id}`, "DELETE");

// Workers
const getWorkers   = () => apiFetch("/api/workers");
const createWorker = (d) => apiFetch("/api/workers", "POST", d);
const updateWorker_ = (id, d) => apiFetch(`/api/workers/${id}`, "PUT", d);
const deleteWorker_ = (id) => apiFetch(`/api/workers/${id}`, "DELETE");

// Materials
const getMaterials    = () => apiFetch("/api/materials");
const createMaterial  = (d) => apiFetch("/api/materials", "POST", d);
const updateMaterial_ = (id, d) => apiFetch(`/api/materials/${id}`, "PUT", d);
const deleteMaterial_ = (id) => apiFetch(`/api/materials/${id}`, "DELETE");

// Equipment
const getEquipment    = () => apiFetch("/api/equipment");
const createEquipment = (d) => apiFetch("/api/equipment", "POST", d);
const updateEquip_    = (id, d) => apiFetch(`/api/equipment/${id}`, "PUT", d);
const deleteEquip_    = (id) => apiFetch(`/api/equipment/${id}`, "DELETE");

// Transactions
const getTransactions    = () => apiFetch("/api/transactions");
const createTransaction  = (d) => apiFetch("/api/transactions", "POST", d);
const deleteTransaction_ = (id) => apiFetch(`/api/transactions/${id}`, "DELETE");

// Safety
const getSafety    = () => apiFetch("/api/safety");
const createSafety = (d) => apiFetch("/api/safety", "POST", d);
