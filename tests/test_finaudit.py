"""
Comprehensive Test Suite for FinAudit AI Multi-Agent AML System
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.transaction import Transaction
from backend.engine.anomaly_detector import AnomalyDetector
from backend.engine.graph_engine import GraphEngine
from backend.tools.sanctions_checker import SanctionsChecker
from backend.tools.regulatory_rag import RegulatoryRAG
from backend.tools.forensics_tools import ForensicsTools
from backend.agents.orchestrator import AMLOrchestrator
from backend.scenarios.scenario_loader import ScenarioLoader

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "FinAudit AI Swarm"
    assert data["available_scenarios"] >= 4


def test_list_scenarios():
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    scenarios = resp.json()
    assert len(scenarios) >= 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "structuring_ring" in scenario_ids
    assert "sanctions_evasion" in scenario_ids
    assert "trade_based_ml" in scenario_ids
    assert "crypto_offramp" in scenario_ids


def test_get_scenario_details():
    resp = client.get("/api/scenarios/structuring_ring")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "structuring_ring"
    assert len(data["transactions"]) >= 6


def test_structuring_anomaly_detection():
    detector = AnomalyDetector()
    txs = ScenarioLoader.load_scenario_transactions("structuring_ring")
    alerts = detector.analyze_transactions(txs)
    
    rule_ids = [a.rule_id for a in alerts]
    assert "AML-TYP-001" in rule_ids  # Structuring / Smurfing detected
    assert any("Structuring" in a.rule_name for a in alerts)


def test_circular_routing_anomaly_detection():
    detector = AnomalyDetector()
    txs = ScenarioLoader.load_scenario_transactions("trade_based_ml")
    alerts = detector.analyze_transactions(txs)
    
    rule_ids = [a.rule_id for a in alerts]
    assert "AML-TYP-006" in rule_ids or "AML-TYP-007" in rule_ids  # Circular Wash or TBML


def test_sanctions_checker_tool():
    checker = SanctionsChecker()
    
    # 1. Sanctioned target
    res1 = checker.screen_entity("Volkov Energy Trading LLC")
    assert res1["is_flagged"] is True
    assert res1["list_type"] == "SANCTIONS"
    assert res1["country"] == "RU"

    # 2. Fuzzy alias target
    res2 = checker.screen_entity("Volkov Group Inc")
    assert res2["is_flagged"] is True

    # 3. Clean target
    res3 = checker.screen_entity("Acme General Supplies Corporation")
    assert res3["is_flagged"] is False
    assert res3["risk_tier"] == "LOW"


def test_regulatory_rag_retrieval():
    rag = RegulatoryRAG()
    results = rag.retrieve_relevant_regulations("smurfing cash deposit threshold evasion", top_k=2)
    assert len(results) > 0
    assert any("Structuring" in r["typology"] for r in results)


def test_graph_engine_construction():
    graph_engine = GraphEngine()
    txs = ScenarioLoader.load_scenario_transactions("structuring_ring")
    G, graph_data = graph_engine.build_graph(txs)
    
    assert len(graph_data.nodes) >= 6
    assert len(graph_data.edges) >= 6
    assert G.number_of_nodes() >= 6


@pytest.mark.asyncio
async def test_full_orchestrator_investigation():
    orchestrator = AMLOrchestrator()
    txs = ScenarioLoader.load_scenario_transactions("sanctions_evasion")
    
    result = await orchestrator.run_investigation(
        transactions=txs,
        scenario_name="Sanctions Evasion Test"
    )
    
    assert result.investigation_id.startswith("INV-")
    assert result.total_transactions == len(txs)
    assert len(result.agent_trace) >= 5
    assert result.sar_draft is not None
    assert result.sar_draft.primary_subject != ""
    assert result.sar_draft.overall_risk_score > 60.0


def test_investigate_api_and_sar_signoff():
    # 1. Run investigation via POST /api/investigate
    payload = {"scenario_id": "structuring_ring"}
    resp = client.post("/api/investigate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    sar_id = data["sar_draft"]["sar_id"]
    assert sar_id.startswith("SAR-")

    # 2. Sign off on SAR
    signoff_payload = {
        "sar_id": sar_id,
        "reviewer_name": "Compliance Director Jane Doe",
        "reviewer_notes": "All alerts verified with law enforcement priority.",
        "decision": "APPROVED"
    }
    signoff_resp = client.post("/api/sar/signoff", json=signoff_payload)
    assert signoff_resp.status_code == 200
    signoff_data = signoff_resp.json()
    assert signoff_data["status"] == "SUCCESS"
    assert "APPROVED" in signoff_data["filing_status"]
