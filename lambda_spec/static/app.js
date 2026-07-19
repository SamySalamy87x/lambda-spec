"use strict";

const $ = (selector) => document.querySelector(selector);
const app = { lang: "en", dataset: null, roles: {}, result: null, narrative: "", api: null };
const copy = {
  en: { datasetReady: "Dataset ready", running: "Computing coupling, trajectory, withdrawal envelope, and drivers…", complete: "Analysis completed successfully.", choose: "Select at least one system column and one environment column.", uploadError: "The CSV could not be read.", explaining: "Interpreting only the evidence in the report…", system: "System", environment: "Environment", ignore: "Ignore", confidence: "confidence", samples: "samples", used: "used rows", states: { robust: "robust", watch: "watch", fragile: "fragile" }, trends: { strengthening: "strengthening", stable: "stable", weakening: "weakening" } },
  es: { datasetReady: "Datos listos", running: "Calculando acoplamiento, trayectoria, retiro e impulsores…", complete: "El análisis terminó correctamente.", choose: "Selecciona al menos una columna de sistema y una de entorno.", uploadError: "No fue posible leer el CSV.", explaining: "Interpretando únicamente la evidencia del reporte…", system: "Sistema", environment: "Entorno", ignore: "Ignorar", confidence: "confianza", samples: "muestras", used: "filas utilizadas", states: { robust: "robusto", watch: "vigilancia", fragile: "frágil" }, trends: { strengthening: "fortaleciéndose", stable: "estable", weakening: "debilitándose" } }
};
const tr = (key) => copy[app.lang][key] ?? key;

function status(message, type = "") { const node = $("#statusMessage"); node.textContent = message || ""; node.className = `status-message ${type}`.trim(); }
function loading(button, active, text) { if (!button.dataset.label) button.dataset.label = button.innerHTML; button.disabled = active; button.innerHTML = active ? `<span class="spinner">◌</span> ${text}` : button.dataset.label; }
async function jsonRequest(url, options = {}) { const response = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } }); const data = await response.json().catch(() => ({})); if (!response.ok) { const error = new Error(data.error || `Request failed (${response.status})`); error.status = response.status; throw error; } return data; }

function inferRoles(dataset) {
  const ratios = dataset.columns.map((_, col) => { const sample = dataset.rows.slice(0, 100); const valid = sample.filter((row) => Number.isFinite(Number(row[col]))).length; return sample.length ? valid / sample.length : 0; });
  const numeric = dataset.columns.filter((name, index) => ratios[index] >= .75 && !/^(time|date|timestamp|index|id)$/i.test(name));
  const roles = Object.fromEntries(dataset.columns.map((name) => [name, "ignore"]));
  const split = Math.max(1, Math.ceil(numeric.length / 2));
  numeric.slice(0, split).forEach((name) => roles[name] = "system");
  numeric.slice(split).forEach((name) => roles[name] = "environment");
  return roles;
}

function configureWindow(value) {
  if (!app.dataset) return;
  const input = $("#windowInput");
  const max = Math.max(3, Math.min(200, app.dataset.rows.length));
  input.max = String(max);
  input.value = String(Math.max(3, Math.min(max, Number(value) || Math.round(app.dataset.rows.length / 5))));
  $("#windowOutput").textContent = `${input.value} rows`;
}

function renderMeta() {
  const d = app.dataset;
  $("#datasetMeta").innerHTML = d ? `<strong>${escapeHtml(d.title || "Dataset")}</strong><br>${d.rows.length.toLocaleString()} ${app.lang === "es" ? "filas" : "rows"} · ${d.columns.length} ${app.lang === "es" ? "columnas" : "columns"}` : "";
}

function renderMapper() {
  const target = $("#columnMapper"); target.innerHTML = "";
  if (!app.dataset) return;
  for (const name of app.dataset.columns) {
    const row = document.createElement("label"); row.className = "column-role";
    row.innerHTML = `<span title="${escapeHtml(name)}">${escapeHtml(name)}</span><select aria-label="Role for ${escapeHtml(name)}"><option value="ignore">${tr("ignore")}</option><option value="system">${tr("system")}</option><option value="environment">${tr("environment")}</option></select>`;
    const select = row.querySelector("select"); select.value = app.roles[name] || "ignore"; select.addEventListener("change", () => { app.roles[name] = select.value; }); target.appendChild(row);
  }
}

async function loadDemo(name = $("#demoSelect").value, auto = true) {
  const button = $("#loadDemoButton"); loading(button, true, "Loading…"); status("");
  try {
    let dataset;
    try { dataset = await jsonRequest(`api/demo?name=${encodeURIComponent(name)}`); app.api = true; }
    catch (error) { dataset = window.LambdaSpecAnalysis.demo(name); app.api = false; }
    app.dataset = dataset; app.roles = Object.fromEntries(dataset.columns.map((name) => [name, "ignore"]));
    (dataset.system_columns || []).forEach((name) => app.roles[name] = "system");
    (dataset.environment_columns || []).forEach((name) => app.roles[name] = "environment");
    $("#titleInput").value = dataset.title || ""; $("#methodSelect").value = dataset.method || "spearman";
    configureWindow(dataset.window); renderMeta(); renderMapper(); status(tr("datasetReady"), "success");
    if (auto) await runAnalysis();
  } catch (error) { status(error.message, "error"); }
  finally { loading(button, false); }
}

function parseCsv(text) {
  const rows = []; let row = []; let value = ""; let quoted = false;
  for (let i = 0; i < text.length; i += 1) { const char = text[i]; if (quoted) { if (char === '"' && text[i + 1] === '"') { value += '"'; i += 1; } else if (char === '"') quoted = false; else value += char; } else if (char === '"') quoted = true; else if (char === ',') { row.push(value.trim()); value = ""; } else if (char === '\n') { row.push(value.trim()); if (row.some((cell) => cell !== "")) rows.push(row); row = []; value = ""; } else if (char !== '\r') value += char; }
  row.push(value.trim()); if (row.some((cell) => cell !== "")) rows.push(row);
  if (rows.length < 4) throw new Error("CSV requires a header and at least 3 rows.");
  const width = rows[0].length; if (width < 2) throw new Error("CSV requires at least 2 columns.");
  return { columns: rows[0].map((name, index) => name || `column_${index + 1}`), rows: rows.slice(1).map((item) => item.concat(Array(Math.max(0, width - item.length)).fill("")).slice(0, width)) };
}

async function handleCsv(file) {
  if (!file) return; if (file.size > 5 * 1024 * 1024) { status("File exceeds 5 MB.", "error"); return; }
  try { const parsed = parseCsv(await file.text()); app.dataset = { ...parsed, title: file.name.replace(/\.csv$/i, ""), source: file.name }; app.roles = inferRoles(app.dataset); $("#titleInput").value = app.dataset.title; configureWindow(); renderMeta(); renderMapper(); status(tr("datasetReady"), "success"); }
  catch (error) { status(`${tr("uploadError")} ${error.message}`, "error"); }
}

function payload() {
  const system = Object.entries(app.roles).filter(([, role]) => role === "system").map(([name]) => name);
  const environment = Object.entries(app.roles).filter(([, role]) => role === "environment").map(([name]) => name);
  if (!system.length || !environment.length) throw new Error(tr("choose"));
  return { ...app.dataset, title: $("#titleInput").value.trim() || app.dataset.title, method: $("#methodSelect").value, window: Number($("#windowInput").value), system_columns: system, environment_columns: environment };
}

async function runAnalysis() {
  if (!app.dataset) return; const button = $("#analyzeButton"); loading(button, true, app.lang === "es" ? "Analizando…" : "Analyzing…"); status(tr("running"));
  try { const input = payload(); let result; try { result = (await jsonRequest("api/analyze", { method: "POST", body: JSON.stringify(input) })).result; app.api = true; } catch (error) { result = window.LambdaSpecAnalysis.analyzeTable(input); app.api = false; } app.result = result; app.narrative = ""; renderResults(); status(tr("complete"), "success"); }
  catch (error) { status(error.message, "error"); }
  finally { loading(button, false); }
}

function renderResults() {
  const r = app.result; if (!r) return;
  $("#emptyState").classList.add("hidden"); $("#results").classList.remove("hidden");
  $("#resultTitle").textContent = r.title; $("#resultContext").textContent = `${r.sample_count} ${tr("samples")} · ${r.method} · ${r.data_quality?.used_rows ?? r.sample_count} ${tr("used")}`;
  $("#lambdaMetric").textContent = r.global.lam.toFixed(3); $("#phiMetric").textContent = r.global.phi.toFixed(3); $("#slopeMetric").textContent = `${r.trajectory.lambda_slope >= 0 ? "+" : ""}${r.trajectory.lambda_slope.toFixed(4)}`;
  $("#trendMetric").textContent = tr("trends")[r.trajectory.trend] || r.trajectory.trend; $("#stateMetric").textContent = tr("states")[r.global.state] || r.global.state; $("#confidenceMetric").textContent = `${Math.round(r.confidence.score * 100)}% ${tr("confidence")}`;
  $("#headlineText").textContent = r.summary.headline; fillList("#evidenceList", r.summary.evidence); fillList("#limitsList", r.summary.limits); renderDrivers(r.drivers); drawTrajectory(r.trajectory.points); drawStress(r.withdrawal);
  $("#narrativeText").textContent = app.narrative || (app.lang === "es" ? "Ejecuta el intérprete después del análisis." : "Run the interpreter after the analysis."); $("#engineLabel").textContent = app.narrative ? (app.api ? "OpenAI / server" : "deterministic / browser") : "—";
  window.setTimeout(() => $("#results").scrollIntoView({ behavior: "smooth", block: "start" }), 80);
}

function fillList(selector, items) { const target = $(selector); target.innerHTML = ""; items.forEach((text) => { const li = document.createElement("li"); li.textContent = text; target.appendChild(li); }); }
function renderDrivers(items) { const target = $("#driversList"); target.innerHTML = ""; if (!items.length) { target.textContent = "No drivers available."; return; } items.forEach((item) => { const row = document.createElement("div"); row.className = "driver-row"; row.innerHTML = `<span class="driver-name">${escapeHtml(item.name)}</span><span class="driver-track"><i class="driver-fill" style="width:${Math.max(2, item.importance * 100)}%"></i></span><span class="driver-value">${(item.importance * 100).toFixed(1)}%</span>`; target.appendChild(row); }); }

function drawLineChart(canvas, series, colors, xLabel) {
  const ratio = window.devicePixelRatio || 1; const width = Math.max(320, canvas.clientWidth || 600); const height = 280; canvas.width = width * ratio; canvas.height = height * ratio; const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
  const pad = { l: 42, r: 18, t: 18, b: 34 }; const w = width - pad.l - pad.r; const h = height - pad.t - pad.b; ctx.font = "11px system-ui"; ctx.strokeStyle = "rgba(190,240,225,.12)"; ctx.fillStyle = "#8fa9a2"; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) { const y = pad.t + h * i / 4; ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke(); ctx.fillText((1 - i / 4).toFixed(2), 5, y + 4); }
  series.forEach((values, si) => { ctx.strokeStyle = colors[si]; ctx.lineWidth = 2.2; ctx.beginPath(); values.forEach((value, index) => { const x = pad.l + (values.length === 1 ? 0 : w * index / (values.length - 1)); const y = pad.t + h * (1 - Math.max(0, Math.min(1, value))); index ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke(); }); ctx.fillStyle = "#8fa9a2"; ctx.fillText(xLabel, Math.max(pad.l, width - 110), height - 9);
}
function drawTrajectory(points) { drawLineChart($("#trajectoryChart"), [points.map((p) => p.lambda), points.map((p) => p.phi)], ["#72f2b2", "#ff8e9f"], app.lang === "es" ? "ventanas →" : "windows →"); }
function drawStress(points) { drawLineChart($("#stressChart"), [points.map((p) => p.lambda)], ["#61d7e5"], app.lang === "es" ? "retiro →" : "withdrawal →"); }

async function explain() {
  if (!app.result) return; const button = $("#explainButton"); loading(button, true, app.lang === "es" ? "Interpretando…" : "Interpreting…"); status(tr("explaining"));
  try { try { const response = await jsonRequest("api/explain", { method: "POST", body: JSON.stringify({ result: app.result, question: $("#questionInput").value, lang: app.lang }) }); app.narrative = response.narrative; $("#engineLabel").textContent = response.engine; app.api = true; } catch (error) { app.narrative = window.LambdaSpecAnalysis.fallbackNarrative(app.result, app.lang); $("#engineLabel").textContent = "deterministic / browser"; app.api = false; } $("#narrativeText").textContent = app.narrative; status(tr("complete"), "success"); }
  catch (error) { status(error.message, "error"); } finally { loading(button, false); }
}

function download(filename, content, type = "text/plain") { const blob = new Blob([content], { type }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 500); }
function slug(value) { return (value || "lambda-spec-report").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char])); }

function switchLanguage() { app.lang = app.lang === "en" ? "es" : "en"; document.documentElement.lang = app.lang; $("#languageButton").textContent = app.lang === "en" ? "ES" : "EN"; renderMeta(); renderMapper(); if (app.result) renderResults(); }

$("#languageButton").addEventListener("click", switchLanguage); $("#loadDemoButton").addEventListener("click", () => loadDemo()); $("#csvInput").addEventListener("change", (event) => handleCsv(event.target.files[0])); $("#windowInput").addEventListener("input", (event) => $("#windowOutput").textContent = `${event.target.value} rows`); $("#analyzeButton").addEventListener("click", runAnalysis); $("#explainButton").addEventListener("click", explain); $("#printButton").addEventListener("click", () => window.print());
$("#downloadJsonButton").addEventListener("click", () => app.result && download(`${slug(app.result.title)}.json`, JSON.stringify(app.result, null, 2), "application/json"));
$("#downloadMarkdownButton").addEventListener("click", () => app.result && download(`${slug(app.result.title)}.md`, window.LambdaSpecAnalysis.markdownReport(app.result, app.narrative), "text/markdown"));
window.addEventListener("resize", () => { if (app.result) { drawTrajectory(app.result.trajectory.points); drawStress(app.result.withdrawal); } });
loadDemo("degradation", true);
