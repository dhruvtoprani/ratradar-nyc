const COLORS = {
  bg: "#100a18",
  panel: "#21162f",
  text: "#d7ccdf",
  acid: "#d8ff4f",
  violet: "#a78bfa",
  orange: "#ffb454",
  coral: "#ff6b7a",
  grid: "rgba(224,204,255,.10)",
};

const state = {
  latest: [],
  history: [],
  metrics: {},
  importance: [],
  geojson: {},
  filteredRows: [],
};

const plotLayout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: COLORS.text, family: "Inter, sans-serif" },
  margin: { l: 46, r: 20, t: 54, b: 45 },
  hoverlabel: { bgcolor: COLORS.panel, font: { color: "#fbf7ff" } },
};

const pct = (value, digits = 1) => `${(Number(value) * 100).toFixed(digits)}%`;
const num = (value, digits = 0) => Number(value ?? 0).toFixed(digits);
const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);

async function loadData() {
  const [latest, history, metrics, importance, geojson] = await Promise.all([
    fetch("./data/latest.json").then((response) => response.json()),
    fetch("./data/history.json").then((response) => response.json()),
    fetch("./data/metrics.json").then((response) => response.json()),
    fetch("./data/importance.json").then((response) => response.json()),
    fetch("./data/nyc_modzcta.geojson").then((response) => response.json()),
  ]);
  state.latest = latest.rows;
  state.history = history.rows;
  state.metrics = metrics;
  state.importance = importance.rows;
  state.geojson = geojson;
  state.filteredRows = [...state.latest];
}

function initNavigation() {
  const activate = (sectionId) => {
    document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === sectionId));
    document.querySelectorAll(".nav-link").forEach((button) => button.classList.toggle("active", button.dataset.section === sectionId));
    window.scrollTo({ top: 0, behavior: "smooth" });
    window.history.replaceState(null, "", `#${sectionId}`);
    window.setTimeout(() => window.dispatchEvent(new Event("resize")), 80);
  };
  document.querySelectorAll(".nav-link").forEach((button) => button.addEventListener("click", () => activate(button.dataset.section)));
  document.querySelectorAll("[data-jump]").forEach((button) => button.addEventListener("click", () => activate(button.dataset.jump)));
  const initial = window.location.hash.slice(1);
  if (initial && document.getElementById(initial)) activate(initial);
}

function renderOverview() {
  const xgb = state.metrics.models.xgboost;
  const averageRisk = state.latest.reduce((sum, row) => sum + row.risk_probability, 0) / state.latest.length;
  const top = [...state.latest].sort((a, b) => b.risk_probability - a.risk_probability);
  const boroughRisk = Object.entries(state.latest.reduce((acc, row) => {
    acc[row.borough] ??= [];
    acc[row.borough].push(row.risk_probability);
    return acc;
  }, {})).map(([borough, values]) => [borough, values.reduce((a, b) => a + b, 0) / values.length])
    .sort((a, b) => b[1] - a[1]);

  document.getElementById("model-version").textContent = state.metrics.model_version;
  document.getElementById("prediction-date").textContent = new Date(`${state.latest[0].prediction_date}T12:00:00`).toLocaleDateString("en-US", { month: "short", day: "2-digit" });
  document.getElementById("citywide-risk").textContent = pct(averageRisk);
  document.getElementById("roc-auc").textContent = xgb.roc_auc.toFixed(3);
  document.getElementById("top-ten-precision").textContent = pct(xgb.top_10_precision);
  document.getElementById("brief-title").textContent = `Priority signals cluster in ${boroughRisk[0][0]} and ${boroughRisk[1][0]}.`;
  document.getElementById("brief-copy").textContent =
    `ZIPs ${top.slice(0, 3).map((row) => row.zip_code).join(", ")} carry the highest modeled surge risk. ` +
    `The current signal is led by ${top[0].top_driver.toLowerCase()} and recent complaint momentum.`;

  document.getElementById("top-risk-list").innerHTML = top.slice(0, 8).map((row, index) => `
    <div class="risk-row">
      <span class="risk-rank">${String(index + 1).padStart(2, "0")}</span>
      <div><strong>${escapeHtml(row.zip_code)} · ${escapeHtml(row.borough)}</strong><small>${escapeHtml(row.top_driver)}</small></div>
      <span class="risk-score">${pct(row.risk_probability)}</span>
    </div>`).join("");

  document.getElementById("map-average-risk").textContent = pct(averageRisk);
  document.getElementById("map-high-count").textContent = state.latest.filter((row) => row.risk_probability >= .6).length;
  document.getElementById("map-highest-zip").textContent = top[0].zip_code;
  document.getElementById("map-highest-driver").textContent = top[0].top_driver;
}

function mapTrace() {
  return {
    type: "choroplethmapbox",
    geojson: state.geojson,
    locations: state.latest.map((row) => row.zip_code),
    z: state.latest.map((row) => row.risk_probability),
    featureidkey: "properties.zip_code",
    text: state.latest.map((row) => `${row.zip_code} · ${row.borough}<br>${pct(row.risk_probability)} · ${row.risk_tier}<br>${row.top_driver}`),
    hovertemplate: "%{text}<extra></extra>",
    marker: { opacity: .82, line: { color: "rgba(16,10,24,.55)", width: .6 } },
    colorbar: { title: "RISK", tickformat: ".0%", thickness: 12, outlinewidth: 0 },
    zmin: 0,
    zmax: 1,
    colorscale: [
      [0, "#281c47"], [.2, "#765ad6"], [.4, "#d8ff4f"],
      [.6, "#ffce69"], [.8, "#ff8a64"], [1, "#ff4f6d"],
    ],
  };
}

function renderMaps() {
  const layout = {
    ...plotLayout,
    margin: { l: 0, r: 0, t: 0, b: 0 },
    mapbox: { style: "carto-darkmatter", center: { lat: 40.7128, lon: -74.006 }, zoom: 8.6 },
  };
  Plotly.newPlot("overview-map", [mapTrace()], { ...layout, height: 490 }, { displayModeBar: false, responsive: true });
  Plotly.newPlot("risk-map-plot", [mapTrace()], { ...layout, height: 680 }, { displayModeBar: false, responsive: true });
}

function metricMarkup(label, value, detail, tone = "acid") {
  return `<article class="metric-card ${tone}"><span>${label}</span><strong>${value}</strong><small>${detail}</small></article>`;
}

function renderZipDrilldown() {
  const select = document.getElementById("zip-select");
  const sorted = [...state.latest].sort((a, b) => b.risk_probability - a.risk_probability);
  select.innerHTML = sorted.map((row) => `<option value="${row.zip_code}">${row.zip_code} · ${row.borough}</option>`).join("");
  select.addEventListener("change", () => updateZip(select.value));
  updateZip(sorted[0].zip_code);
}

function updateZip(zipCode) {
  const current = state.latest.find((row) => row.zip_code === zipCode);
  document.getElementById("zip-metrics").innerHTML = [
    metricMarkup("Surge Risk", pct(current.risk_probability), current.risk_tier, "coral"),
    metricMarkup("Last 7 Days", num(current.rodent_count_last_7d), "Rodent complaints"),
    metricMarkup("8-Week Baseline", num(current.rodent_rolling_mean_8w, 1), "Complaints per week", "orange"),
    metricMarkup("Complaint Velocity", pct(current.rodent_velocity_7d_vs_30d, 0), "Versus monthly pace", "violet"),
  ].join("");
  document.getElementById("zip-brief-eyebrow").textContent = `${current.borough} · ${current.top_driver}`;
  document.getElementById("zip-brief-title").textContent = `Why ZIP ${zipCode}?`;
  document.getElementById("zip-brief-copy").textContent = current.why_this_zip;

  const history = state.history.filter((row) => row.zip_code === zipCode).sort((a, b) => a.prediction_date.localeCompare(b.prediction_date));
  Plotly.react("complaint-chart", [
    { type: "bar", name: "Weekly complaints", x: history.map((row) => row.prediction_date), y: history.map((row) => row.future_rodent_count_7d), marker: { color: COLORS.acid }, opacity: .72 },
    { type: "scatter", mode: "lines", name: "8-week baseline", x: history.map((row) => row.prediction_date), y: history.map((row) => row.rodent_rolling_mean_8w), line: { color: COLORS.coral, width: 2 } },
  ], { ...plotLayout, title: "Complaint volume vs. baseline", height: 390, xaxis: { gridcolor: COLORS.grid }, yaxis: { gridcolor: COLORS.grid } }, { displayModeBar: false, responsive: true });
  Plotly.react("risk-chart", [
    { type: "scatter", mode: "lines", fill: "tozeroy", x: history.map((row) => row.prediction_date), y: history.map((row) => row.risk_probability), line: { color: COLORS.violet, width: 2 }, fillcolor: "rgba(167,139,250,.18)" },
  ], { ...plotLayout, title: "Modeled surge probability", height: 390, xaxis: { gridcolor: COLORS.grid }, yaxis: { tickformat: ".0%", range: [0, 1], gridcolor: COLORS.grid } }, { displayModeBar: false, responsive: true });
}

function renderModel() {
  const xgb = state.metrics.models.xgboost;
  document.getElementById("model-metrics").innerHTML = [
    metricMarkup("ROC-AUC", xgb.roc_auc.toFixed(3), "Ranking discrimination"),
    metricMarkup("PR-AUC", xgb.pr_auc.toFixed(3), "Positive-class quality", "orange"),
    metricMarkup("F1", xgb.f1.toFixed(3), "Thresholded balance", "violet"),
    metricMarkup("Top-10 Precision", xgb.top_10_precision.toFixed(3), "Weekly priority queue", "coral"),
  ].join("");

  const modelColors = { xgboost: COLORS.acid, logistic_regression: COLORS.violet };
  const rocTraces = Object.entries(state.metrics.models).map(([name, model]) => ({
    type: "scatter", mode: "lines", name: name.replaceAll("_", " "),
    x: model.roc_curve.false_positive_rate, y: model.roc_curve.true_positive_rate,
    line: { color: modelColors[name], width: 3 },
  }));
  rocTraces.push({ type: "scatter", mode: "lines", name: "random", x: [0, 1], y: [0, 1], line: { color: "#6f617d", dash: "dash" } });
  Plotly.newPlot("roc-chart", rocTraces, { ...plotLayout, title: "ROC curve", height: 390, xaxis: { title: "False positive rate", gridcolor: COLORS.grid }, yaxis: { title: "True positive rate", gridcolor: COLORS.grid } }, { displayModeBar: false, responsive: true });

  const prTraces = Object.entries(state.metrics.models).map(([name, model]) => ({
    type: "scatter", mode: "lines", name: name.replaceAll("_", " "),
    x: model.precision_recall_curve.recall, y: model.precision_recall_curve.precision,
    line: { color: name === "xgboost" ? COLORS.coral : COLORS.violet, width: 3 },
  }));
  Plotly.newPlot("pr-chart", prTraces, { ...plotLayout, title: "Precision–recall curve", height: 390, xaxis: { title: "Recall", gridcolor: COLORS.grid }, yaxis: { title: "Precision", gridcolor: COLORS.grid } }, { displayModeBar: false, responsive: true });

  const importance = [...state.importance].slice(0, 14).reverse();
  Plotly.newPlot("importance-chart", [{
    type: "bar", orientation: "h", x: importance.map((row) => row.importance), y: importance.map((row) => row.feature),
    marker: { color: importance.map((_, index) => index / importance.length), colorscale: [[0, "#765ad6"], [.55, "#a78bfa"], [1, "#d8ff4f"]] },
  }], { ...plotLayout, title: "Global XGBoost feature importance", height: 520, xaxis: { gridcolor: COLORS.grid }, yaxis: { automargin: true } }, { displayModeBar: false, responsive: true });
}

function renderExplorer() {
  const borough = document.getElementById("borough-filter");
  const tier = document.getElementById("tier-filter");
  borough.innerHTML = ["All", ...new Set(state.latest.map((row) => row.borough))].sort().map((value) => `<option>${value}</option>`).join("");
  tier.innerHTML = ["All", "Critical", "High", "Elevated", "Watch", "Low"].map((value) => `<option>${value}</option>`).join("");
  borough.addEventListener("change", filterExplorer);
  tier.addEventListener("change", filterExplorer);
  document.getElementById("download-csv").addEventListener("click", downloadCsv);
  filterExplorer();
}

function filterExplorer() {
  const borough = document.getElementById("borough-filter").value;
  const tier = document.getElementById("tier-filter").value;
  state.filteredRows = state.latest.filter((row) => (borough === "All" || row.borough === borough) && (tier === "All" || row.risk_tier === tier))
    .sort((a, b) => b.risk_probability - a.risk_probability);
  document.getElementById("row-count").textContent = state.filteredRows.length;
  document.getElementById("explorer-body").innerHTML = state.filteredRows.map((row) => `
    <tr>
      <td><strong>${escapeHtml(row.zip_code)}</strong></td><td>${escapeHtml(row.borough)}</td>
      <td>${pct(row.risk_probability)}</td><td><span class="tier ${row.risk_tier}">${row.risk_tier}</span></td>
      <td>${num(row.rodent_count_last_7d)}</td><td>${pct(row.rodent_velocity_7d_vs_30d, 0)}</td>
      <td>${escapeHtml(row.top_driver)}</td>
    </tr>`).join("");
}

function downloadCsv() {
  const headers = ["zip_code", "borough", "risk_probability", "risk_tier", "rodent_count_last_7d", "rodent_velocity_7d_vs_30d", "top_driver"];
  const csv = [headers.join(","), ...state.filteredRows.map((row) => headers.map((header) => JSON.stringify(row[header] ?? "")).join(","))].join("\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  link.download = "ratradar-latest-predictions.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function init() {
  initNavigation();
  await loadData();
  renderOverview();
  renderMaps();
  renderZipDrilldown();
  renderModel();
  renderExplorer();
  document.getElementById("loading").classList.add("hidden");
}

window.addEventListener("DOMContentLoaded", () => {
  init().catch((error) => {
    console.error(error);
    document.getElementById("loading").innerHTML = `<strong>Unable to load the RatRadar release.</strong><small>${escapeHtml(error.message)}</small>`;
  });
});

