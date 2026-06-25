/* ====================================================
   BILANCIO — API ADAPTER
   Fetcha da FastAPI e rimappa nella forma che il rendering
   esistente (DATA.categories / DATA.movements) già usa.
   Cambia API_BASE_URL per puntare al backend in produzione.
==================================================== */
// API_BASE_URL e APP_PASSWORD vengono iniettati a runtime da /api/config
// (Vercel serverless function che legge le variabili d'ambiente)
let API_BASE_URL = "";
let APP_PASSWORD = "";

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", "X-App-Password": APP_PASSWORD },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    throw new Error(`API ${res.status}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

/* ---------- CATEGORIE ---------- */
function categoryFromAPI(c) {
  return { id: c.id, name: c.name, type: c.type, color: c.color, limit: c.monthly_limit || 0 };
}
function categoryToAPI(c) {
  return { name: c.name, type: c.type, color: c.color, monthly_limit: c.limit || null };
}

async function loadCategoriesFromAPI() {
  const rows = await apiRequest("/categories");
  return rows.map(categoryFromAPI);
}
async function createCategoryAPI(localCat) {
  const row = await apiRequest("/categories", {
    method: "POST",
    body: JSON.stringify(categoryToAPI(localCat)),
  });
  return categoryFromAPI(row);
}
async function updateCategoryAPI(id, partialLocalCat) {
  const row = await apiRequest(`/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify(categoryToAPI(partialLocalCat)),
  });
  return categoryFromAPI(row);
}
async function deleteCategoryAPI(id) {
  await apiRequest(`/categories/${id}`, { method: "DELETE" });
}

/* ---------- CONTI ---------- */
function accountFromAPI(a) {
  return { id: a.id, name: a.name, type: a.type, saldo: Number(a.initial_balance), color: a.color };
}
function accountToAPI(a) {
  return { name: a.name, type: a.type, initial_balance: a.saldo, color: a.color };
}

async function loadAccountsFromAPI() {
  const rows = await apiRequest("/accounts");
  return rows.map(accountFromAPI);
}
async function createAccountAPI(localAccount) {
  const row = await apiRequest("/accounts", {
    method: "POST",
    body: JSON.stringify(accountToAPI(localAccount)),
  });
  return accountFromAPI(row);
}
async function updateAccountAPI(id, partialLocalAccount) {
  const row = await apiRequest(`/accounts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(accountToAPI(partialLocalAccount)),
  });
  return accountFromAPI(row);
}
async function deleteAccountAPI(id) {
  await apiRequest(`/accounts/${id}`, { method: "DELETE" });
}

/* ---------- PERSONE ----------
   Il resto del codice tratta DATA.persone come un semplice array di nomi
   (non di oggetti {id,name}, eredità del prototipo originale). Manteniamo
   quella forma e teniamo la mappa nome->id solo qui, per le chiamate API.
*/
let personIdByName = {};

async function loadPersonsFromAPI() {
  const rows = await apiRequest("/persons");
  personIdByName = Object.fromEntries(rows.map((p) => [p.name, p.id]));
  return rows.map((p) => p.name);
}
async function createPersonAPI(name) {
  const row = await apiRequest("/persons", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  personIdByName[row.name] = row.id;
  return row.name;
}
async function renamePersonAPI(oldName, newName) {
  const id = personIdByName[oldName];
  const row = await apiRequest(`/persons/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name: newName }),
  });
  delete personIdByName[oldName];
  personIdByName[row.name] = row.id;
  return row.name;
}
async function deletePersonAPI(name) {
  const id = personIdByName[name];
  await apiRequest(`/persons/${id}`, { method: "DELETE" });
  delete personIdByName[name];
}

/* ---------- HELPER CONDIVISO CONTO <-> NOME ----------
   account_name/person_name/from_account_name/to_account_name sono testo nel
   backend. Risolviamo il nome conto <-> id locale usando l'elenco DATA.conti
   passato a queste funzioni — la persona invece è già un nome semplice anche
   nel prototipo originale, nessuna risoluzione necessaria.
*/
function contoIdByName(name, contiList) {
  return name ? (contiList.find((c) => c.name === name)?.id ?? null) : null;
}
function nameByContoId(id, contiList) {
  return id ? (contiList.find((c) => c.id === id)?.name ?? null) : null;
}

/* ---------- MOVIMENTI ---------- */
function movementFromAPI(m, contiList) {
  return {
    id: m.id,
    type: m.type,
    desc: m.description,
    amount: Number(m.amount),
    category: m.category_id,
    conto: contoIdByName(m.account_name, contiList),
    persona: m.person_name || null,
    date: m.date,
    fromConto: contoIdByName(m.from_account_name, contiList),
    toConto: contoIdByName(m.to_account_name, contiList),
  };
}
function movementToAPI(m, contiList) {
  return {
    type: m.type,
    description: m.desc,
    amount: m.amount,
    date: m.date,
    category_id: m.category || null,
    account_name: nameByContoId(m.conto, contiList),
    person_name: m.persona || null,
    from_account_name: nameByContoId(m.fromConto, contiList),
    to_account_name: nameByContoId(m.toConto, contiList),
  };
}

async function loadMovementsFromAPI(filters = {}, contiList = []) {
  const params = new URLSearchParams();
  if (filters.type) params.set("type", filters.type);
  if (filters.category_id) params.set("category_id", filters.category_id);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  const rows = await apiRequest(`/movements${qs ? `?${qs}` : ""}`);
  return rows.map((m) => movementFromAPI(m, contiList));
}
async function createMovementAPI(localMov, contiList) {
  const row = await apiRequest("/movements", {
    method: "POST",
    body: JSON.stringify(movementToAPI(localMov, contiList)),
  });
  return movementFromAPI(row, contiList);
}
async function updateMovementAPI(id, localMov, contiList) {
  const row = await apiRequest(`/movements/${id}`, {
    method: "PATCH",
    body: JSON.stringify(movementToAPI(localMov, contiList)),
  });
  return movementFromAPI(row, contiList);
}
async function deleteMovementAPI(id) {
  await apiRequest(`/movements/${id}`, { method: "DELETE" });
}

/* ---------- RICORRENTI ---------- */
function recurringFromAPI(r, contiList) {
  return {
    id: r.id,
    name: r.name,
    type: r.type,
    amount: Number(r.amount),
    category: r.category_id,
    conto: contoIdByName(r.account_name, contiList),
    persona: r.person_name || null,
    dayOfMonth: r.day_of_month,
    startDate: r.start_date,
    endDate: r.end_date,
    active: r.active,
    lastGeneratedDate: r.last_generated_date,
  };
}
function recurringToAPI(r, contiList) {
  return {
    name: r.name,
    type: r.type,
    amount: r.amount,
    category_id: r.category || null,
    account_name: nameByContoId(r.conto, contiList),
    person_name: r.persona || null,
    day_of_month: r.dayOfMonth,
    start_date: r.startDate,
    end_date: r.endDate || null,
    active: r.active,
  };
}

async function loadRecurringFromAPI(contiList = []) {
  const rows = await apiRequest("/recurring");
  return rows.map((r) => recurringFromAPI(r, contiList));
}
async function createRecurringAPI(localRec, contiList) {
  const row = await apiRequest("/recurring", {
    method: "POST",
    body: JSON.stringify(recurringToAPI(localRec, contiList)),
  });
  return recurringFromAPI(row, contiList);
}
async function updateRecurringAPI(id, partialLocalRec, contiList) {
  const row = await apiRequest(`/recurring/${id}`, {
    method: "PATCH",
    body: JSON.stringify(recurringToAPI(partialLocalRec, contiList)),
  });
  return recurringFromAPI(row, contiList);
}
async function deleteRecurringAPI(id) {
  await apiRequest(`/recurring/${id}`, { method: "DELETE" });
}
async function runDueRecurringAPI(contiList = []) {
  const rows = await apiRequest("/recurring/run-due", { method: "POST" });
  return rows.map((m) => movementFromAPI(m, contiList));
}

/* ---------- OBIETTIVI ---------- */
function goalFromAPI(g) {
  return {
    id: g.id,
    name: g.name,
    target: Number(g.target),
    current: Number(g.current),
    deadline: g.deadline || null,
  };
}
function goalToAPI(g) {
  return {
    name: g.name,
    target: g.target,
    current: g.current ?? 0,
    deadline: g.deadline || null,
  };
}

async function loadGoalsFromAPI() {
  const rows = await apiRequest("/goals");
  return rows.map(goalFromAPI);
}
async function createGoalAPI(localGoal) {
  const row = await apiRequest("/goals", {
    method: "POST",
    body: JSON.stringify(goalToAPI(localGoal)),
  });
  return goalFromAPI(row);
}
async function updateGoalAPI(id, partial) {
  const row = await apiRequest(`/goals/${id}`, {
    method: "PATCH",
    body: JSON.stringify(partial),
  });
  return goalFromAPI(row);
}
async function deleteGoalAPI(id) {
  await apiRequest(`/goals/${id}`, { method: "DELETE" });
}

/* ---------- INVESTIMENTI ---------- */
function investmentFromAPI(inv) {
  return {
    id: inv.id,
    ticker: inv.ticker,
    isin: inv.isin || null,
    name: inv.name,
    type: inv.type,
    sector: inv.sector,
    qty: Number(inv.qty),
    avgPrice: Number(inv.avg_price),
    curPrice: Number(inv.cur_price),
    addedAt: inv.added_at,
    updatedAt: inv.updated_at,
  };
}
function investmentToAPI(inv) {
  return {
    ticker: inv.ticker,
    isin: inv.isin || null,
    name: inv.name,
    type: inv.type,
    sector: inv.sector,
    qty: inv.qty,
    avg_price: inv.avgPrice,
    cur_price: inv.curPrice,
  };
}

async function loadInvestmentsFromAPI() {
  const rows = await apiRequest("/investments");
  return rows.map(investmentFromAPI);
}
async function createInvestmentAPI(localInv) {
  const row = await apiRequest("/investments", {
    method: "POST",
    body: JSON.stringify(investmentToAPI(localInv)),
  });
  return investmentFromAPI(row);
}
async function updateInvestmentAPI(id, partial) {
  const row = await apiRequest(`/investments/${id}`, {
    method: "PATCH",
    body: JSON.stringify(partial),
  });
  return investmentFromAPI(row);
}
async function deleteInvestmentAPI(id) {
  await apiRequest(`/investments/${id}`, { method: "DELETE" });
}

/* ---------- IMPOSTAZIONI ---------- */
async function loadSettingsAPI() {
  return await apiRequest("/settings");
}
async function saveSettingsAPI(data) {
  return await apiRequest("/settings", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/* ---------- ARCHIVIO ---------- */
async function loadArchiveYearsAPI() {
  return await apiRequest("/archive/years");
}
async function exportArchiveYearAPI(year) {
  return await apiRequest(`/archive/${year}`);
}
async function deleteArchiveYearAPI(year) {
  return await apiRequest(`/archive/${year}`, { method: "DELETE" });
}
