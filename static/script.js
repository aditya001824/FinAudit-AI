/**
 * FinAudit AI - War Room Client Application Logic
 * Integrates Vis.js graph visualization, SSE real-time agent reasoning, and SAR document rendering.
 */

let networkInstance = null;
let currentInvestigationResult = null;
let currentScenarioId = "structuring_ring";
let currentScenariosList = [];

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await checkHealth();
    await loadScenarios();
}

function setupEventListeners() {
    const scenarioSelect = document.getElementById("scenarioSelect");
    const startInvestigateBtn = document.getElementById("startInvestigateBtn");
    const viewSarBtn = document.getElementById("viewSarBtn");
    const closeSarModalBtn = document.getElementById("closeSarModalBtn");
    const approveSarBtn = document.getElementById("approveSarBtn");
    const downloadSarJsonBtn = document.getElementById("downloadSarJsonBtn");
    const sarModal = document.getElementById("sarModal");

    scenarioSelect.addEventListener("change", (e) => {
        currentScenarioId = e.target.value;
        onScenarioSelected(currentScenarioId);
    });

    startInvestigateBtn.addEventListener("click", () => {
        startInvestigationStream(currentScenarioId);
    });

    viewSarBtn.addEventListener("click", () => {
        if (currentInvestigationResult && currentInvestigationResult.sar_draft) {
            openSarModal(currentInvestigationResult.sar_draft);
        }
    });

    closeSarModalBtn.addEventListener("click", () => {
        sarModal.classList.remove("open");
    });

    approveSarBtn.addEventListener("click", () => {
        signOffSar();
    });

    downloadSarJsonBtn.addEventListener("click", () => {
        downloadSarDossier();
    });
}

async function checkHealth() {
    try {
        const resp = await fetch("/api/health");
        if (resp.ok) {
            const data = await resp.json();
            const providerBadge = document.getElementById("providerBadge");
            if (providerBadge) {
                providerBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> Engine: ${data.llm_provider.toUpperCase()}`;
            }
        }
    } catch (err) {
        console.warn("Health check failed:", err);
    }
}

async function loadScenarios() {
    try {
        const resp = await fetch("/api/scenarios");
        const scenarios = await resp.json();
        currentScenariosList = scenarios;

        const select = document.getElementById("scenarioSelect");
        select.innerHTML = "";

        scenarios.forEach((sc) => {
            const opt = document.createElement("option");
            opt.value = sc.id;
            opt.textContent = `${sc.name} (${sc.severity})`;
            select.appendChild(opt);
        });

        if (scenarios.length > 0) {
            currentScenarioId = scenarios[0].id;
            select.value = currentScenarioId;
            onScenarioSelected(currentScenarioId);
        }
    } catch (err) {
        console.error("Failed to load scenarios:", err);
    }
}

async function onScenarioSelected(scenarioId) {
    try {
        const resp = await fetch(`/api/scenarios/${scenarioId}`);
        const scenario = await resp.json();

        // Update Banner
        document.getElementById("bannerTitle").textContent = scenario.name;
        document.getElementById("bannerDesc").textContent = scenario.description;
        const sevBadge = document.getElementById("bannerSeverity");
        sevBadge.textContent = `${scenario.severity} SEVERITY`;
        sevBadge.className = `badge severity-badge ${scenario.severity === "CRITICAL" ? "text-danger" : "text-warning"}`;

        // Populate Ledger Table
        renderTransactionLedger(scenario.transactions);

        // Reset metrics
        const totalVol = scenario.transactions.reduce((acc, tx) => acc + tx.amount, 0);
        document.getElementById("metricTotalVol").textContent = `$${totalVol.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        document.getElementById("metricSuspVol").textContent = "$0.00";
        document.getElementById("metricTypologies").textContent = "0";
        document.getElementById("metricRiskScore").textContent = "-- / 100";

        // Reset agent feed and alerts
        resetFeed();
        document.getElementById("viewSarBtn").disabled = true;

        // Render initial simple graph
        renderInitialGraph(scenario.transactions);

    } catch (err) {
        console.error("Failed to load scenario details:", err);
    }
}

function renderTransactionLedger(transactions) {
    const tbody = document.getElementById("txTableBody");
    const countBadge = document.getElementById("txCountBadge");
    tbody.innerHTML = "";
    countBadge.textContent = `${transactions.length} Transactions`;

    transactions.forEach((tx) => {
        const tr = document.createElement("tr");

        let flagsHtml = "";
        if (tx.risk_flags && tx.risk_flags.length > 0) {
            flagsHtml = tx.risk_flags.map(f => `<span class="badge badge-flag">${f}</span>`).join(" ");
        } else {
            flagsHtml = `<span class="badge badge-info">NORMAL</span>`;
        }

        tr.innerHTML = `
            <td><code>${tx.id}</code></td>
            <td>${tx.timestamp.replace('T', ' ').replace('Z', '')}</td>
            <td><strong>${tx.source_entity}</strong> (${tx.source_country})</td>
            <td><strong>${tx.target_entity}</strong> (${tx.target_country})</td>
            <td class="tx-amount">$${tx.amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${tx.currency}</td>
            <td><span class="badge badge-info">${tx.transaction_type}</span></td>
            <td>${flagsHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function resetFeed() {
    const feed = document.getElementById("agentFeed");
    feed.innerHTML = `
        <div class="empty-state" id="feedEmptyState">
            <i class="fa-solid fa-satellite-dish"></i>
            <p>Ready to deploy multi-agent investigation swarm.</p>
            <span>Agents will execute ReAct loops, query OFAC/PEP watchlists, retrieve FinCEN statutes, and draft audit reports in real time.</span>
        </div>
    `;
    const alerts = document.getElementById("alertsContainer");
    alerts.innerHTML = `<div class="empty-state-sm"><span>No anomalies triggered yet.</span></div>`;
}

function startInvestigationStream(scenarioId) {
    const startBtn = document.getElementById("startInvestigateBtn");
    const viewSarBtn = document.getElementById("viewSarBtn");
    const agentPulse = document.getElementById("agentPulse");
    const feed = document.getElementById("agentFeed");

    startBtn.disabled = true;
    startBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Swarm Investigating...`;
    agentPulse.classList.add("active");
    agentPulse.querySelector(".pulse-text").textContent = "SWARM ACTIVE";

    feed.innerHTML = ""; // Clear feed

    const eventSource = new EventSource(`/api/investigate/stream?scenario_id=${scenarioId}`);

    eventSource.addEventListener("start", (e) => {
        const data = JSON.parse(e.data);
        console.log("Investigation Started:", data);
    });

    eventSource.addEventListener("anomalies_detected", (e) => {
        const data = JSON.parse(e.data);
        renderAnomalies(data.anomalies);
        document.getElementById("metricTypologies").textContent = data.count;
    });

    eventSource.addEventListener("agent_thought", (e) => {
        const thought = JSON.parse(e.data);
        appendAgentThought(thought);
    });

    eventSource.addEventListener("complete", (e) => {
        const result = JSON.parse(e.data);
        currentInvestigationResult = result;
        eventSource.close();

        // Update UI
        startBtn.disabled = false;
        startBtn.innerHTML = `<i class="fa-solid fa-brain-circuit"></i> Re-Run Swarm Investigation`;
        agentPulse.classList.remove("active");
        agentPulse.querySelector(".pulse-text").textContent = "COMPLETE";
        viewSarBtn.disabled = false;

        // Update metrics
        if (result.sar_draft) {
            document.getElementById("metricSuspVol").textContent = `$${result.sar_draft.total_suspicious_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
            document.getElementById("metricRiskScore").textContent = `${result.sar_draft.overall_risk_score} / 100`;
        }

        // Render final enriched forensic graph
        if (result.graph_data) {
            renderEnrichedGraph(result.graph_data);
        }
    });

    eventSource.addEventListener("error", (e) => {
        console.error("SSE Error:", e);
        eventSource.close();
        startBtn.disabled = false;
        startBtn.innerHTML = `<i class="fa-solid fa-brain-circuit"></i> Launch Multi-Agent Investigation`;
        agentPulse.classList.remove("active");
        agentPulse.querySelector(".pulse-text").textContent = "ERROR";
    });
}

function appendAgentThought(thought) {
    const feed = document.getElementById("agentFeed");
    
    let stepClass = "thought-card";
    if (thought.action === "EXECUTE_TOOL") stepClass += " tool-step";
    if (thought.action === "SYNTHESIS_AND_CONCLUSION") stepClass += " synthesis-step";
    if (thought.action === "GENERATE_SAR_FILING") stepClass += " sar-step";

    const card = document.createElement("div");
    card.className = stepClass;

    let toolHtml = "";
    if (thought.tool) {
        toolHtml = `
            <div class="tool-badge-row">
                <i class="fa-solid fa-screwdriver-wrench"></i> Tool: <strong>${thought.tool}</strong>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="thought-header">
            <div class="step-title-group">
                <span class="step-num">STEP ${thought.step}</span>
                <span class="agent-name">${thought.agent_name}</span>
            </div>
            <span class="action-type">${thought.action}</span>
        </div>
        ${toolHtml}
        <div class="thought-text">"${thought.thought}"</div>
        <div class="observation-box">
            <i class="fa-solid fa-circle-check"></i> ${thought.observation || 'Action completed successfully.'}
        </div>
    `;

    feed.appendChild(card);
    feed.scrollTop = feed.scrollHeight;
}

function renderAnomalies(anomalies) {
    const container = document.getElementById("alertsContainer");
    container.innerHTML = "";

    if (!anomalies || anomalies.length === 0) {
        container.innerHTML = `<div class="empty-state-sm"><span>No heuristic anomalies flagged.</span></div>`;
        return;
    }

    anomalies.forEach((a) => {
        const item = document.createElement("div");
        item.className = "anomaly-alert-item";
        item.innerHTML = `
            <div class="alert-top-row">
                <span class="alert-rule-name"><i class="fa-solid fa-triangle-exclamation"></i> ${a.rule_name}</span>
                <span class="badge ${a.severity === 'CRITICAL' ? 'severity-badge' : 'badge-flag'}">${a.severity}</span>
            </div>
            <p class="alert-desc">${a.description}</p>
        `;
        container.appendChild(item);
    });
}

/* Graph Visualization via Vis.js */
function renderInitialGraph(transactions) {
    const nodesMap = new Map();
    const edges = [];

    transactions.forEach((tx, idx) => {
        if (!nodesMap.has(tx.source_entity)) {
            nodesMap.set(tx.source_entity, {
                id: tx.source_entity,
                label: `${tx.source_entity}\n(${tx.source_country})`,
                color: { background: "#10b981", border: "#059669", highlight: { background: "#34d399", border: "#10b981" } },
                font: { color: "#ffffff", size: 12, face: "Inter" },
                shape: "box",
                margin: 10
            });
        }
        if (!nodesMap.has(tx.target_entity)) {
            nodesMap.set(tx.target_entity, {
                id: tx.target_entity,
                label: `${tx.target_entity}\n(${tx.target_country})`,
                color: { background: "#10b981", border: "#059669", highlight: { background: "#34d399", border: "#10b981" } },
                font: { color: "#ffffff", size: 12, face: "Inter" },
                shape: "box",
                margin: 10
            });
        }

        edges.push({
            id: `edge_${idx}`,
            from: tx.source_entity,
            to: tx.target_entity,
            label: `$${tx.amount.toLocaleString()}`,
            arrows: "to",
            color: { color: "#38bdf8", highlight: "#0284c7" },
            font: { color: "#94a3b8", size: 10, align: "middle", face: "JetBrains Mono" },
            smooth: { type: "curvedCW", roundness: 0.15 }
        });
    });

    drawVisNetwork(Array.from(nodesMap.values()), edges);
}

function renderEnrichedGraph(graphData) {
    const nodes = graphData.nodes.map(n => {
        let bgColor = "#10b981"; // Clean Green
        let borderColor = "#059669";

        if (n.risk_level === "critical" || n.sanctioned) {
            bgColor = "#ef4444"; // Red
            borderColor = "#b91c1c";
        } else if (n.risk_level === "high" || n.pep) {
            bgColor = "#f59e0b"; // Orange/Amber
            borderColor = "#d97706";
        } else if (n.risk_level === "medium") {
            bgColor = "#3b82f6"; // Blue
            borderColor = "#2563eb";
        }

        const tag = n.sanctioned ? " [SANCTIONED]" : (n.pep ? " [PEP]" : "");

        return {
            id: n.id,
            label: `${n.label}${tag}\n(${n.country})`,
            color: {
                background: bgColor,
                border: borderColor,
                highlight: { background: bgColor, border: "#ffffff" }
            },
            font: { color: "#ffffff", size: 12, face: "Inter", bold: n.sanctioned || n.pep },
            shape: "box",
            margin: 12,
            shadow: n.sanctioned || n.pep
        };
    });

    const edges = graphData.edges.map(e => {
        const isFlagged = e.is_flagged;
        return {
            id: e.id,
            from: e.source,
            to: e.target,
            label: e.label,
            arrows: "to",
            color: {
                color: isFlagged ? "#ef4444" : "#38bdf8",
                highlight: isFlagged ? "#f87171" : "#0284c7"
            },
            width: isFlagged ? 2.5 : 1.5,
            dashes: isFlagged,
            font: { color: isFlagged ? "#fca5a5" : "#94a3b8", size: 11, align: "top", face: "JetBrains Mono" },
            smooth: { type: "curvedCW", roundness: 0.2 }
        };
    });

    drawVisNetwork(nodes, edges);
}

function drawVisNetwork(nodes, edges) {
    const container = document.getElementById("networkGraph");
    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };

    const options = {
        nodes: {
            borderWidth: 2,
            shadow: true
        },
        edges: {
            shadow: false
        },
        physics: {
            solver: "forceAtlas2Based",
            forceAtlas2Based: {
                gravitationalConstant: -70,
                centralGravity: 0.015,
                springLength: 160,
                springConstant: 0.08
            },
            stabilization: { iterations: 120 }
        },
        interaction: {
            hover: true,
            zoomView: true,
            dragView: true
        }
    };

    if (networkInstance) {
        networkInstance.destroy();
    }
    networkInstance = new vis.Network(container, data, options);
}

/* SAR Modal & Actions */
function openSarModal(sar) {
    document.getElementById("modalSarId").textContent = `FinCEN Form 111 — ${sar.sar_id}`;
    document.getElementById("modalFilingDate").textContent = `Filing Date: ${sar.filing_date} | Generated by FinAudit AI Swarm`;
    document.getElementById("sarSubject").textContent = sar.primary_subject;
    document.getElementById("sarTotalAmount").textContent = `$${sar.total_suspicious_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${sar.currency}`;
    document.getElementById("sarRiskScore").textContent = `${sar.overall_risk_score} / 100`;
    
    const statusBadge = document.getElementById("sarStatusBadge");
    statusBadge.textContent = sar.status;
    statusBadge.className = `badge ${sar.status.includes("APPROVED") ? "badge-info" : "badge-flag"}`;

    document.getElementById("sarNarrativeBox").textContent = sar.narrative_summary;

    // Timeline
    const timelineBox = document.getElementById("sarTimelineBox");
    timelineBox.innerHTML = "";
    (sar.chronological_timeline || []).forEach(evt => {
        const row = document.createElement("div");
        row.className = `timeline-row ${evt.is_flagged ? 'flagged' : ''}`;
        row.innerHTML = `[${evt.timestamp}] ${evt.flow} <em>(${evt.description || 'N/A'})</em>`;
        timelineBox.appendChild(row);
    });

    // Citations
    const citationsList = document.getElementById("sarCitationsList");
    citationsList.innerHTML = "";
    (sar.regulatory_violations || []).forEach(cit => {
        const li = document.createElement("li");
        li.textContent = cit;
        citationsList.appendChild(li);
    });

    // Actions
    const actionsList = document.getElementById("sarActionsList");
    actionsList.innerHTML = "";
    (sar.recommended_actions || []).forEach(act => {
        const li = document.createElement("li");
        li.textContent = act;
        actionsList.appendChild(li);
    });

    document.getElementById("sarModal").classList.add("open");
}

async function signOffSar() {
    if (!currentInvestigationResult || !currentInvestigationResult.sar_draft) return;
    
    const sarId = currentInvestigationResult.sar_draft.sar_id;
    const reviewerName = document.getElementById("reviewerName").value || "Senior AML Officer";
    
    try {
        const resp = await fetch("/api/sar/signoff", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sar_id: sarId,
                reviewer_name: reviewerName,
                reviewer_notes: "Approved after autonomous multi-agent verification and sanctions screening.",
                decision: "APPROVED_AND_TRANSMITTED"
            })
        });

        if (resp.ok) {
            const data = await resp.json();
            currentInvestigationResult.sar_draft.status = data.filing_status;
            document.getElementById("sarStatusBadge").textContent = data.filing_status;
            document.getElementById("sarStatusBadge").className = "badge badge-info";
            alert(`✅ SAR ${sarId} successfully approved and signed off by ${reviewerName}!`);
        }
    } catch (err) {
        console.error("Sign-off error:", err);
        alert("Failed to submit sign-off.");
    }
}

function downloadSarDossier() {
    if (!currentInvestigationResult) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentInvestigationResult, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `FinAudit_Dossier_${currentInvestigationResult.investigation_id}.json`);
    dlAnchor.click();
}
