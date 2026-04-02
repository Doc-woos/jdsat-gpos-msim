const state = {
  catalog: [],
  catalogByName: {},
  projection: null,
  comparison: null,
  libraryRecords: [],
};

const runScenarioSelect = document.getElementById("run-scenario-select");
const compareBaselineSelect = document.getElementById("compare-baseline-select");
const compareVariantSelect = document.getElementById("compare-variant-select");
const runCatalogNote = document.getElementById("run-catalog-note");
const compareCatalogNote = document.getElementById("compare-catalog-note");
const runStatus = document.getElementById("run-status");
const compareStatus = document.getElementById("compare-status");
const projectionTitle = document.getElementById("projection-title");
const comparisonTitle = document.getElementById("comparison-title");
const projectionMetrics = document.getElementById("projection-metrics");
const comparisonMetrics = document.getElementById("comparison-metrics");
const projectionInsights = document.getElementById("projection-insights");
const comparisonInsights = document.getElementById("comparison-insights");
const projectionExportSummary = document.getElementById("projection-export-summary");
const comparisonExportSummary = document.getElementById("comparison-export-summary");
const projectionTable = document.getElementById("projection-table");
const comparisonTable = document.getElementById("comparison-table");
const projectionMeta = document.getElementById("projection-meta");
const comparisonHighlights = document.getElementById("comparison-highlights");
const librarySummary = document.getElementById("library-summary");
const libraryTable = document.getElementById("library-table");
const exportCatalog = document.getElementById("export-catalog");
const metricTemplate = document.getElementById("metric-card-template");

function setStatus(element, message, mode = "idle") {
  element.textContent = message;
  element.classList.remove("status-idle", "status-ready", "status-error", "status-working", "delta-negative");
  if (mode === "error") {
    element.classList.add("status-error", "delta-negative");
    return;
  }
  if (mode === "ready") {
    element.classList.add("status-ready");
    return;
  }
  if (mode === "working") {
    element.classList.add("status-working");
    return;
  }
  element.classList.add("status-idle");
}

function cloneMetric(label, value) {
  const node = metricTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".metric-label").textContent = label;
  node.querySelector(".metric-value").textContent = value;
  return node;
}

function populateSelect(select, entries) {
  select.replaceChildren();
  for (const entry of entries) {
    const option = document.createElement("option");
    option.value = entry.scenario_name;
    option.textContent = entry.label;
    select.appendChild(option);
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function loadCatalog() {
  const payload = await fetchJson("/api/projection/catalog");
  state.catalog = payload.scenarios;
  state.catalogByName = Object.fromEntries(payload.scenarios.map((entry) => [entry.scenario_name, entry]));
  populateSelect(runScenarioSelect, state.catalog);
  populateSelect(compareBaselineSelect, state.catalog);
  populateSelect(compareVariantSelect, state.catalog);
  compareVariantSelect.selectedIndex = Math.min(1, state.catalog.length - 1);
  updateRunCatalogNote();
  updateCompareCatalogNote();
}

async function loadLibrary() {
  const payload = await fetchJson("/api/library/records");
  state.libraryRecords = payload.records;
  renderLibrary();
}

async function loadExportCatalog() {
  const payload = await fetchJson("/api/projection/export-catalog");
  renderExportCatalog(payload.exports);
}

function renderExportCatalog(exports) {
  exportCatalog.replaceChildren(...exports.map((entry) => buildExportCard(entry)));
  exportCatalog.classList.remove("empty");
}

function buildExportCard(entry) {
  const card = document.createElement("article");
  card.className = "card reference-card";
  const eyebrow = document.createElement("p");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = `${entry.scope} ? ${entry.format.toUpperCase()}`;
  const heading = document.createElement("h3");
  heading.className = "reference-title";
  heading.textContent = entry.label;
  const body = document.createElement("p");
  body.className = "page-copy";
  body.textContent = entry.description;
  const endpoint = document.createElement("p");
  endpoint.className = "export-note";
  endpoint.textContent = entry.endpoint;
  card.append(eyebrow, heading, body, endpoint);
  return card;
}

function renderLibrary() {
  const counts = {
    scenario: 0,
    projection_run: 0,
    comparison_run: 0,
  };
  for (const record of state.libraryRecords) {
    if (record.kind in counts) {
      counts[record.kind] += 1;
    }
  }

  librarySummary.replaceChildren(
    cloneMetric("Saved Scenarios", counts.scenario),
    cloneMetric("Saved Runs", counts.projection_run),
    cloneMetric("Saved Comparisons", counts.comparison_run),
    cloneMetric("Total Records", state.libraryRecords.length),
  );
  librarySummary.classList.remove("empty");

  if (!state.libraryRecords.length) {
    libraryTable.textContent = "No saved records yet.";
    libraryTable.classList.add("empty");
    return;
  }
  libraryTable.innerHTML = buildTable(
    ["Saved At", "Kind", "Label", "Scenario", "Path"],
    state.libraryRecords.slice(0, 12).map((record) => [
      record.saved_at,
      kindBadge(record.kind),
      record.label,
      record.variant_scenario_id ? `${record.scenario_id} -> ${record.variant_scenario_id}` : record.scenario_id,
      `<span class="path-chip">${record.path}</span>`,
    ]),
  );
  libraryTable.classList.remove("empty");
}

function describeCatalogEntry(entry) {
  if (!entry) {
    return "";
  }
  const source = entry.source ? `Source: ${entry.source}. ` : "";
  const notes = entry.notes || "No analyst note recorded.";
  return `${entry.label} · ${entry.processing_rule}. ${source}${notes}`;
}

function updateRunCatalogNote() {
  runCatalogNote.textContent = describeCatalogEntry(state.catalogByName[runScenarioSelect.value]);
}

function updateCompareCatalogNote() {
  const baseline = state.catalogByName[compareBaselineSelect.value];
  const variant = state.catalogByName[compareVariantSelect.value];
  if (!baseline || !variant) {
    compareCatalogNote.textContent = "Pick two named fixtures to compare.";
    return;
  }
  compareCatalogNote.textContent = `Baseline: ${baseline.label}. Variant: ${variant.label}.`;
}

function renderProjection(result) {
  state.projection = result;
  const label = result.metadata.scenario_metadata.label || result.scenario_id;
  projectionTitle.textContent = `${label} · ${result.metadata.processing_rule}`;

  projectionMetrics.replaceChildren(
    cloneMetric("Inventory", result.metrics.total_inventory),
    cloneMetric("Demand", result.metrics.total_demand),
    cloneMetric("Gap", result.metrics.total_gap),
    cloneMetric("Fingerprint", result.metadata.scenario_fingerprint.slice(0, 8)),
  );

  projectionExportSummary.textContent = projectionExportSummaryText(result);
  projectionExportSummary.classList.remove("empty");

  projectionInsights.replaceChildren(
    buildInsightCard("Grade Balance", "Grouped readiness by grade", result.summary.by_grade.map((item) => `${item.key}: ${item.inventory}/${item.demand} (${signed(item.gap)})`)),
    buildInsightCard("Specialty Balance", "Grouped readiness by specialty", result.summary.by_specialty.map((item) => `${item.key}: ${item.inventory}/${item.demand} (${signed(item.gap)})`)),
    buildInsightCard("Community Fill", communityFillSubtitle(result.summary.authorization_basis), fillSummaryLines(result.summary.fill_by_community), "negative"),
    buildInsightCard("Force Element Fill", "Grouped inventory vs authorization by force element", fillSummaryLines(result.summary.fill_by_force_element), "negative"),
    buildInsightCard("Readiness Pressure", readinessSubtitle(result.summary.authorization_basis), readinessSignalLines(result.summary.readiness_signals), "negative"),
    buildInsightCard("Top Shortages", "Greatest negative gaps", result.summary.largest_shortages.map((item) => `${item.cell_id}: ${item.inventory}/${item.demand} (${signed(item.gap)})`), "negative"),
    buildInsightCard("Top Overages", "Largest positive gaps", result.summary.largest_overages.map((item) => `${item.cell_id}: ${item.inventory}/${item.demand} (${signed(item.gap)})`), "positive"),
  );
  projectionInsights.classList.remove("empty");

  projectionTable.innerHTML = buildTable(
    ["Cell", "Specialty", "Grade", "Inventory", "Demand", "Gap"],
    result.projected_inventory.map((item) => [
      item.cell_id,
      item.specialty,
      item.grade,
      item.inventory,
      item.demand,
      decorateDelta(item.gap),
    ]),
  );
  projectionTable.classList.remove("empty");

  projectionMeta.innerHTML = "";
  const entries = [
    ["Label", result.metadata.scenario_metadata.label || result.scenario_id],
    ["Version", result.metadata.scenario_metadata.version],
    ["Created By", result.metadata.scenario_metadata.created_by || "-"],
    ["Source", result.metadata.scenario_metadata.source || "-"],
    ["Notes", result.metadata.scenario_metadata.notes || "-"],
    ["Rule", result.metadata.processing_rule],
    ["Decision", result.metadata.decision_ref],
    ["Checkpoint", result.metadata.checkpoint_ref],
    ["Run Time", result.metadata.run_timestamp],
    ["Fingerprint", result.metadata.scenario_fingerprint],
    ["Policies", summarisePolicy(result.metadata.policy_summary)],
    ["Auth Basis", summariseAuthorizationBasis(result.summary.authorization_basis)],
  ];
  for (const [labelText, value] of entries) {
    const dt = document.createElement("dt");
    dt.textContent = labelText;
    const dd = document.createElement("dd");
    dd.textContent = value;
    projectionMeta.append(dt, dd);
  }
  projectionMeta.classList.remove("empty");
}

function renderComparison(comparison) {
  state.comparison = comparison;
  const baselineLabel = comparison.baseline.metadata.scenario_metadata.label || comparison.baseline.scenario_id;
  const variantLabel = comparison.variant.metadata.scenario_metadata.label || comparison.variant.scenario_id;
  comparisonTitle.textContent = `${baselineLabel} vs ${variantLabel}`;

  comparisonMetrics.replaceChildren(
    cloneMetric("Inventory Delta", comparison.inventory_delta),
    cloneMetric("Gap Delta", comparison.gap_delta),
    cloneMetric("Rule", comparison.summary.rule_change ? "Changed" : "Same"),
    cloneMetric("Variant", comparison.variant.metadata.scenario_fingerprint.slice(0, 8)),
  );

  comparisonExportSummary.textContent = comparisonExportSummaryText(comparison);
  comparisonExportSummary.classList.remove("empty");

  comparisonInsights.replaceChildren(
    buildInsightCard("Rule Difference", comparison.summary.rule_change ? "Execution semantics changed" : "Execution semantics unchanged", [comparison.summary.rule_summary], comparison.summary.rule_change ? "positive" : null),
    buildInsightCard("Inventory Gains", "Largest cell increases", comparison.summary.largest_inventory_gains.map((item) => `${item.cell_id}: ${signed(item.inventory_delta)}`), "positive"),
    buildInsightCard("Inventory Losses", "Largest cell decreases", comparison.summary.largest_inventory_losses.map((item) => `${item.cell_id}: ${signed(item.inventory_delta)}`), "negative"),
    buildInsightCard("Community Shift", comparisonAuthorizationSubtitle(comparison.summary.authorization_basis), topAggregateLines(comparison.summary.by_community), "positive"),
    buildInsightCard("Force Element Shift", "Largest force-element inventory changes", topAggregateLines(comparison.summary.by_force_element), "positive"),
    buildInsightCard("Gap Improvements", "Most improved shortages", comparison.summary.largest_gap_improvements.map((item) => `${item.cell_id}: ${signed(item.gap_delta)}`), "positive"),
    buildInsightCard("Gap Worsenings", "Most degraded shortages", comparison.summary.largest_gap_worsenings.map((item) => `${item.cell_id}: ${signed(item.gap_delta)}`), "negative"),
  );
  comparisonInsights.classList.remove("empty");

  const topRows = comparison.cell_deltas.slice().sort((left, right) => Math.abs(right.inventory_delta) - Math.abs(left.inventory_delta)).slice(0, 6);
  comparisonTable.innerHTML = buildTable(
    ["Cell", "Inventory Delta", "Gap Delta"],
    topRows.map((item) => [item.cell_id, decorateDelta(item.inventory_delta), decorateDelta(item.gap_delta)]),
  );
  comparisonTable.classList.remove("empty");

  const sections = [
    buildHighlightCard("Rule Summary", [comparison.summary.rule_summary]),
    buildHighlightCard("Auth Basis", comparisonAuthorizationLines(comparison.summary.authorization_basis)),
    buildPolicyDeltaCard(comparison.summary.policy_deltas),
    buildDriverCard(comparison.summary.drivers),
    buildAggregateDeltaCard("Community Deltas", comparison.summary.by_community),
    buildAggregateDeltaCard("Force Element Deltas", comparison.summary.by_force_element),
    buildHighlightCard("Largest Inventory Gains", comparison.summary.largest_inventory_gains.map((item) => `${item.cell_id}: ${signed(item.inventory_delta)}`)),
    buildHighlightCard("Largest Gap Improvements", comparison.summary.largest_gap_improvements.map((item) => `${item.cell_id}: ${signed(item.gap_delta)}`)),
  ];
  comparisonHighlights.replaceChildren(...sections);
  comparisonHighlights.classList.remove("empty");
}

function buildTable(headers, rows) {
  const head = headers.map((header) => `<th>${header}</th>`).join("");
  const body = rows.map((row) => `<tr class="data-row">${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("");
  return `<div class="table-scroller"><table class="data-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function buildHighlightCard(title, lines) {
  const card = document.createElement("section");
  card.className = "highlight-card";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const list = document.createElement("ul");
  for (const line of lines.length ? lines : ["No entries."]) {
    const li = document.createElement("li");
    li.innerHTML = line;
    list.appendChild(li);
  }
  card.append(heading, list);
  return card;
}

function buildInsightCard(title, subtitle, lines, tone = null) {
  const card = document.createElement("section");
  card.className = "insight-card";
  if (tone) {
    card.classList.add(`insight-${tone}`);
  }
  const eyebrow = document.createElement("p");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "Insight";
  const heading = document.createElement("h3");
  heading.className = "reference-title";
  heading.textContent = title;
  const detail = document.createElement("p");
  detail.className = "page-copy insight-copy";
  detail.textContent = subtitle;
  const list = document.createElement("div");
  list.className = "signal-list";
  for (const line of lines.length ? lines : ["No entries."]) {
    const item = document.createElement("span");
    item.className = "signal-chip";
    item.textContent = line;
    list.appendChild(item);
  }
  card.append(eyebrow, heading, detail, list);
  return card;
}

function buildPolicyDeltaCard(policyDeltas) {
  const lines = policyDeltas.map((item) => `${item.category}: ${item.baseline_count} -> ${item.variant_count} (${signed(item.delta)})`);
  return buildHighlightCard("Policy Deltas", lines);
}

function buildDriverCard(drivers) {
  const lines = drivers.map((driver) => `<strong>${driver.title}</strong>: ${driver.detail}`);
  return buildHighlightCard("Why It Changed", lines);
}

function buildAggregateDeltaCard(title, deltas) {
  const lines = topAggregateLines(deltas, 6);
  return buildHighlightCard(title, lines);
}

function fillSummaryLines(summaries, count = 4) {
  return summaries
    .slice(0, count)
    .map((item) => `${item.key} ${Math.round(item.fill_rate * 100)}% fill (${signed(item.gap)}) [${item.status}]`);
}

function summariseAuthorizationBasis(basis) {
  if (!basis) {
    return "none";
  }
  if (basis.source === "authorization") {
    return basis.artifact_id ? `explicit authorization (${basis.artifact_id})` : "explicit authorization";
  }
  if (basis.source === "demand_proxy") {
    return "demand proxy";
  }
  return "unavailable";
}

function communityFillSubtitle(basis) {
  if (!basis || basis.source === "none") {
    return "Grouped inventory vs authorization by community";
  }
  if (basis.source === "authorization") {
    return "Grouped inventory vs explicit authorization by community";
  }
  return "Grouped inventory vs demand-proxy authorization by community";
}

function readinessSubtitle(basis) {
  if (!basis || basis.source === "none") {
    return "Repo-local grouped fill signals";
  }
  if (basis.source === "authorization") {
    return "Repo-local grouped fill signals using explicit authorization";
  }
  return "Repo-local grouped fill signals using demand-proxy authorization";
}

function comparisonAuthorizationSubtitle(basis) {
  if (!basis) {
    return "Largest community inventory changes";
  }
  return basis.description;
}

function comparisonAuthorizationLines(basis) {
  if (!basis) {
    return ["No authorization provenance available."];
  }
  return [
    `Baseline: ${summariseAuthorizationBasis(basis.baseline)}`,
    `Variant: ${summariseAuthorizationBasis(basis.variant)}`,
    basis.description,
  ];
}

function readinessSignalLines(signals, count = 4) {
  return signals
    .slice(0, count)
    .map((item) => `${item.group_type}:${item.key} ${Math.round(item.fill_rate * 100)}% fill (${signed(item.gap)}) [${item.status}]`);
}

function topAggregateLines(deltas, count = 3) {
  return deltas
    .slice()
    .sort((left, right) => Math.abs(right.inventory_delta) - Math.abs(left.inventory_delta))
    .slice(0, count)
    .map((item) => `${item.key}: ${signed(item.inventory_delta)} inv, ${signed(item.gap_delta)} gap`);
}

function decorateDelta(value) {
  const className = value > 0 ? "delta-positive" : value < 0 ? "delta-negative" : "";
  return `<span class="${className}">${signed(value)}</span>`;
}

function signed(value) {
  return value > 0 ? `+${value}` : `${value}`;
}

function kindBadge(kind) {
  const labelMap = {
    scenario: "scenario",
    projection_run: "run",
    comparison_run: "comparison",
  };
  const styleKind = labelMap[kind] || kind;
  const label = kind.replace(/_/g, " ");
  return `<span class="kind-badge kind-${styleKind}">${label}</span>`;
}

function summarisePolicy(policySummary) {
  return [
    `${policySummary.rate_table_entries} rate tables`,
    `${policySummary.rate_overrides} rate overrides`,
    `${policySummary.accession_table_entries} accession tables`,
    `${policySummary.accession_overrides} accession overrides`,
  ].join(" | ");
}

function projectionExportReadyMessage(artifact, format) {
  if (format === "csv") {
    return `Exported ${artifact.filename} with grouped fill and readiness sections when available.`;
  }
  return `Exported ${artifact.filename}.`;
}

function comparisonExportReadyMessage(artifact, format) {
  if (format === "csv") {
    return `Exported ${artifact.filename} with grouped deltas plus baseline and variant fill/readiness sections when available.`;
  }
  return `Exported ${artifact.filename}.`;
}

function projectionSummaryExportReadyMessage(artifact) {
  return `Exported ${artifact.filename} with compact grouped projection summaries.`;
}

function comparisonSummaryExportReadyMessage(artifact) {
  return `Exported ${artifact.filename} with compact grouped comparison summaries.`;
}

function projectionExportSummaryText(result) {
  const sections = ["cell inventory rows"];
  if (result.summary.fill_by_occfld.length) {
    sections.push("fill by OccFld");
  }
  if (result.summary.fill_by_community.length) {
    sections.push("fill by community");
  }
  if (result.summary.fill_by_force_element.length) {
    sections.push("fill by force element");
  }
  if (result.summary.readiness_signals.length) {
    sections.push("readiness signals");
  }
  return `Projection CSV will include ${sections.join(", ")}. Authorization basis: ${summariseAuthorizationBasis(result.summary.authorization_basis)}.`;
}

function comparisonExportSummaryText(comparison) {
  const sections = ["cell deltas", "grouped deltas"];
  if (comparison.baseline.summary.fill_by_community.length || comparison.variant.summary.fill_by_community.length) {
    sections.push("baseline and variant grouped fill");
  }
  if (comparison.baseline.summary.readiness_signals.length || comparison.variant.summary.readiness_signals.length) {
    sections.push("baseline and variant readiness signals");
  }
  return `${sections.join(", ")}. Baseline auth basis: ${summariseAuthorizationBasis(comparison.summary.authorization_basis.baseline)}. Variant auth basis: ${summariseAuthorizationBasis(comparison.summary.authorization_basis.variant)}.`;
}

function downloadArtifact(artifact) {
  const blob = new Blob([artifact.content], { type: artifact.media_type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = artifact.filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function runProjection() {
  const scenarioName = runScenarioSelect.value;
  const entry = state.catalogByName[scenarioName];
  setStatus(runStatus, `Running ${entry ? entry.label : scenarioName}...`, "working");
  try {
    const payload = await fetchJson(`/api/projection/scenarios/${scenarioName}`);
    renderProjection(payload.result);
    setStatus(runStatus, `Loaded ${entry ? entry.label : scenarioName}.`, "ready");
  } catch (error) {
    setStatus(runStatus, error.message, "error");
  }
}

async function runComparison() {
  const baselineScenarioName = compareBaselineSelect.value;
  const variantScenarioName = compareVariantSelect.value;
  const baselineEntry = state.catalogByName[baselineScenarioName];
  const variantEntry = state.catalogByName[variantScenarioName];
  setStatus(compareStatus, `Comparing ${baselineEntry ? baselineEntry.label : baselineScenarioName} vs ${variantEntry ? variantEntry.label : variantScenarioName}...`, "working");
  try {
    const payload = await fetchJson("/api/projection/compare-named", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName }),
    });
    renderComparison(payload.comparison);
    setStatus(compareStatus, `Compared ${baselineEntry ? baselineEntry.label : baselineScenarioName} vs ${variantEntry ? variantEntry.label : variantScenarioName}.`, "ready");
  } catch (error) {
    setStatus(compareStatus, error.message, "error");
  }
}

async function fetchScenarioDefinition(name) {
  const payload = await fetchJson(`/api/projection/scenarios/${name}/definition`);
  return payload.scenario;
}

async function saveScenario() {
  const scenarioName = runScenarioSelect.value;
  const scenario = await fetchScenarioDefinition(scenarioName);
  const payload = await fetchJson("/api/library/scenarios/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  await loadLibrary();
  setStatus(runStatus, `Saved scenario snapshot ${payload.record.record_id}.`, "ready");
}

async function saveRun() {
  const scenarioName = runScenarioSelect.value;
  const scenario = await fetchScenarioDefinition(scenarioName);
  const payload = await fetchJson("/api/library/runs/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario }),
  });
  await loadLibrary();
  setStatus(runStatus, `Saved run ${payload.record.record_id}.`, "ready");
}

async function saveComparison() {
  const baselineScenarioName = compareBaselineSelect.value;
  const variantScenarioName = compareVariantSelect.value;
  const payload = await fetchJson("/api/library/comparisons/save-named", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName }),
  });
  await loadLibrary();
  setStatus(compareStatus, `Saved comparison ${payload.record.record_id}.`, "ready");
}

async function exportProjection(format) {
  const scenarioName = runScenarioSelect.value;
  const entry = state.catalogByName[scenarioName];
  setStatus(runStatus, `Exporting ${entry ? entry.label : scenarioName} as ${format.toUpperCase()}...`, "working");
  try {
    const [definitionPayload, resultPayload] = await Promise.all([
      fetchScenarioDefinition(scenarioName),
      fetchJson(`/api/projection/scenarios/${scenarioName}`),
    ]);
    const payload = await fetchJson("/api/projection/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: definitionPayload, format }),
    });
    renderProjection(resultPayload.result);
    downloadArtifact(payload.artifact);
    setStatus(runStatus, projectionExportReadyMessage(payload.artifact, format), "ready");
  } catch (error) {
    setStatus(runStatus, error.message, "error");
  }
}

async function exportProjectionSummary() {
  const scenarioName = runScenarioSelect.value;
  const entry = state.catalogByName[scenarioName];
  setStatus(runStatus, `Exporting compact summary for ${entry ? entry.label : scenarioName}...`, "working");
  try {
    const payload = await fetchJson(`/api/projection/scenarios/${scenarioName}/export-summary`);
    const resultPayload = await fetchJson(`/api/projection/scenarios/${scenarioName}`);
    renderProjection(resultPayload.result);
    downloadArtifact(payload.artifact);
    setStatus(runStatus, projectionSummaryExportReadyMessage(payload.artifact), "ready");
  } catch (error) {
    setStatus(runStatus, error.message, "error");
  }
}

async function exportComparison(format) {
  const baselineScenarioName = compareBaselineSelect.value;
  const variantScenarioName = compareVariantSelect.value;
  const baselineEntry = state.catalogByName[baselineScenarioName];
  const variantEntry = state.catalogByName[variantScenarioName];
  setStatus(compareStatus, `Exporting ${baselineEntry ? baselineEntry.label : baselineScenarioName} vs ${variantEntry ? variantEntry.label : variantScenarioName} as ${format.toUpperCase()}...`, "working");
  try {
    const [comparisonPayload, payload] = await Promise.all([
      fetchJson("/api/projection/compare-named", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName }),
      }),
      fetchJson("/api/projection/compare-named-export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName, format }),
      }),
    ]);
    renderComparison(comparisonPayload.comparison);
    downloadArtifact(payload.artifact);
    setStatus(compareStatus, comparisonExportReadyMessage(payload.artifact, format), "ready");
  } catch (error) {
    setStatus(compareStatus, error.message, "error");
  }
}

async function exportComparisonSummary() {
  const baselineScenarioName = compareBaselineSelect.value;
  const variantScenarioName = compareVariantSelect.value;
  const baselineEntry = state.catalogByName[baselineScenarioName];
  const variantEntry = state.catalogByName[variantScenarioName];
  setStatus(compareStatus, `Exporting compact summary for ${baselineEntry ? baselineEntry.label : baselineScenarioName} vs ${variantEntry ? variantEntry.label : variantScenarioName}...`, "working");
  try {
    const [comparisonPayload, payload] = await Promise.all([
      fetchJson("/api/projection/compare-named", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName }),
      }),
      fetchJson("/api/projection/compare-named-export-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseline_scenario_name: baselineScenarioName, variant_scenario_name: variantScenarioName }),
      }),
    ]);
    renderComparison(comparisonPayload.comparison);
    downloadArtifact(payload.artifact);
    setStatus(compareStatus, comparisonSummaryExportReadyMessage(payload.artifact), "ready");
  } catch (error) {
    setStatus(compareStatus, error.message, "error");
  }
}

async function boot() {
  try {
    await Promise.all([loadCatalog(), loadLibrary(), loadExportCatalog()]);
    setStatus(runStatus, "Ready.", "ready");
    setStatus(compareStatus, "Ready.", "ready");
  } catch (error) {
    setStatus(runStatus, error.message, "error");
    setStatus(compareStatus, error.message, "error");
  }
}

runScenarioSelect.addEventListener("change", updateRunCatalogNote);
compareBaselineSelect.addEventListener("change", updateCompareCatalogNote);
compareVariantSelect.addEventListener("change", updateCompareCatalogNote);
document.getElementById("refresh-scenarios").addEventListener("click", boot);
document.getElementById("refresh-library").addEventListener("click", loadLibrary);
document.getElementById("run-scenario").addEventListener("click", runProjection);
document.getElementById("save-scenario").addEventListener("click", () => saveScenario().catch((error) => setStatus(runStatus, error.message, "error")));
document.getElementById("save-run").addEventListener("click", () => saveRun().catch((error) => setStatus(runStatus, error.message, "error")));
document.getElementById("run-comparison").addEventListener("click", runComparison);
document.getElementById("save-comparison").addEventListener("click", () => saveComparison().catch((error) => setStatus(compareStatus, error.message, "error")));
document.getElementById("export-projection-json").addEventListener("click", () => exportProjection("json"));
document.getElementById("export-projection-csv").addEventListener("click", () => exportProjection("csv"));
document.getElementById("export-projection-summary-csv").addEventListener("click", exportProjectionSummary);
document.getElementById("export-comparison-json").addEventListener("click", () => exportComparison("json"));
document.getElementById("export-comparison-csv").addEventListener("click", () => exportComparison("csv"));
document.getElementById("export-comparison-summary-csv").addEventListener("click", exportComparisonSummary);

boot();






