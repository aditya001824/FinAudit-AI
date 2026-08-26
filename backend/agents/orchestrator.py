"""
AML Multi-Agent Orchestrator
Coordinates the end-to-end multi-agent investigation lifecycle and event streaming.
"""
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, AsyncGenerator
from backend.models.transaction import (
    Transaction,
    AnomalyAlert,
    AgentThought,
    SARDraft,
    InvestigationResult,
    GraphData
)
from backend.engine.anomaly_detector import AnomalyDetector
from backend.engine.graph_engine import GraphEngine
from backend.agents.investigator_agent import InvestigatorAgent
from backend.agents.sar_drafter_agent import SARDrafterAgent
from backend.agents.llm_client import LLMClient

class AMLOrchestrator:
    def __init__(self, provider: str = "auto"):
        self.llm_client = LLMClient(provider=provider)
        self.anomaly_detector = AnomalyDetector()
        self.graph_engine = GraphEngine()
        self.investigator_agent = InvestigatorAgent(llm_client=self.llm_client)
        self.sar_drafter_agent = SARDrafterAgent(llm_client=self.llm_client)

    async def run_investigation(
        self,
        transactions: List[Transaction],
        scenario_name: str = "Ad-hoc Investigation",
        focus_entity: Optional[str] = None
    ) -> InvestigationResult:
        """
        Run complete synchronous/asynchronous investigation and return final result.
        """
        investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        # 1. Run Anomaly Engine
        anomalies = self.anomaly_detector.analyze_transactions(transactions)
        
        # 2. Run Investigator Agent
        agent_thoughts, dossier = await self.investigator_agent.investigate(
            transactions=transactions,
            anomalies=anomalies,
            focus_entity=focus_entity
        )
        
        # 3. Run SAR Drafter Agent
        sar_thought, sar_draft = await self.sar_drafter_agent.draft_sar(
            dossier=dossier,
            transactions=transactions,
            scenario_name=scenario_name
        )
        agent_thoughts.append(sar_thought)
        
        # 4. Construct Graph Data
        flagged_tx_ids = set()
        for a in anomalies:
            flagged_tx_ids.update(a.transactions_involved)
            
        sanctioned_entities = set([s["matched_name"] for s in dossier.get("sanctions_hits", []) if s.get("matched_name")])
        pep_entities = set([p["matched_name"] for p in dossier.get("pep_hits", []) if p.get("matched_name")])

        _, graph_data = self.graph_engine.build_graph(
            transactions=transactions,
            flagged_tx_ids=flagged_tx_ids,
            sanctioned_entities=sanctioned_entities,
            pep_entities=pep_entities
        )

        return InvestigationResult(
            investigation_id=investigation_id,
            scenario_name=scenario_name,
            total_transactions=len(transactions),
            flagged_transactions_count=dossier.get("flagged_transaction_count", len(flagged_tx_ids)),
            high_risk_entities_count=len(dossier.get("primary_suspects", [])),
            anomalies=anomalies,
            agent_trace=agent_thoughts,
            sar_draft=sar_draft,
            graph_data=graph_data
        )

    async def stream_investigation(
        self,
        transactions: List[Transaction],
        scenario_name: str = "Real-Time Investigation",
        focus_entity: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream progressive thought steps, tool calls, and final artifacts via SSE.
        """
        investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        
        yield {
            "event": "start",
            "data": {
                "investigation_id": investigation_id,
                "scenario_name": scenario_name,
                "total_transactions": len(transactions),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        await asyncio.sleep(0.3)

        # Stage 1: Ingestion & Anomaly Detection
        anomalies = self.anomaly_detector.analyze_transactions(transactions)
        yield {
            "event": "anomalies_detected",
            "data": {
                "count": len(anomalies),
                "anomalies": [a.model_dump() for a in anomalies]
            }
        }
        await asyncio.sleep(0.4)

        # Stage 2: Agentic Investigation Steps
        all_suspect_entities = list(set([e for a in anomalies for e in a.entities_involved]))
        if focus_entity and focus_entity not in all_suspect_entities:
            all_suspect_entities.append(focus_entity)

        # Agent Step 1: Hypothesis
        t1 = AgentThought(
            agent_name="Forensic Investigator Agent",
            step=1,
            action="PLAN_AND_HYPOTHESIZE",
            thought="Reviewing incoming anomaly telemetry and establishing primary investigation hypotheses.",
            observation=f"Flagged {len(anomalies)} structural anomalies across entities: {', '.join(all_suspect_entities[:5])}."
        )
        yield {"event": "agent_thought", "data": t1.model_dump()}
        await asyncio.sleep(0.5)

        # Agent Step 2: Sanctions screening
        screening_results = self.investigator_agent.sanctions_tool.batch_screen(all_suspect_entities)
        sanctioned_found = [k for k, v in screening_results.items() if v.get("is_flagged") and v.get("list_type") == "SANCTIONS"]
        pep_found = [k for k, v in screening_results.items() if v.get("is_flagged") and v.get("list_type") == "PEP"]
        
        t2 = AgentThought(
            agent_name="Forensic Investigator Agent",
            step=2,
            action="EXECUTE_TOOL",
            tool="Sanctions & PEP Screening Tool",
            tool_input={"entities_screened": all_suspect_entities},
            tool_output={"sanctioned": sanctioned_found, "pep": pep_found},
            thought=f"Executing global sanctions and PEP screening on {len(all_suspect_entities)} identified counterparties.",
            observation=f"Found {len(sanctioned_found)} sanctioned entities and {len(pep_found)} PEPs."
        )
        yield {"event": "agent_thought", "data": t2.model_dump()}
        await asyncio.sleep(0.5)

        # Agent Step 3: Flow & Profiling
        flow_summary = self.investigator_agent.forensics_tool.calculate_flow_of_funds(transactions)
        entity_profiles = {ent: self.investigator_agent.forensics_tool.build_entity_profile(ent, transactions) for ent in all_suspect_entities}
        primary_suspect = all_suspect_entities[0] if all_suspect_entities else "Unknown Subject"
        if sanctioned_found:
            primary_suspect = sanctioned_found[0]

        t3 = AgentThought(
            agent_name="Forensic Investigator Agent",
            step=3,
            action="EXECUTE_TOOL",
            tool="Entity Profiler & Flow Reconstructor",
            tool_input={"primary_suspect": primary_suspect},
            tool_output={"total_network_volume": flow_summary["total_volume_usd"]},
            thought=f"Reconstructing flow-of-funds network and deep-profiling '{primary_suspect}'.",
            observation=f"Identified '{primary_suspect}' as central hub with ${entity_profiles.get(primary_suspect, {}).get('total_inflow_amount', 0):,.2f} inflow."
        )
        yield {"event": "agent_thought", "data": t3.model_dump()}
        await asyncio.sleep(0.5)

        # Agent Step 4: Regulatory RAG
        query_terms = " ".join([a.rule_name for a in anomalies]) + (" SANCTIONS" if sanctioned_found else "")
        reg_citations = self.investigator_agent.rag_tool.retrieve_relevant_regulations(query_terms, top_k=3)

        t4 = AgentThought(
            agent_name="Forensic Investigator Agent",
            step=4,
            action="EXECUTE_TOOL",
            tool="Regulatory RAG Knowledge Base",
            tool_input={"query": query_terms},
            tool_output={"statutes": [r["id"] for r in reg_citations]},
            thought="Querying Bank Secrecy Act and FATF knowledge base for applicable legal mandates.",
            observation=f"Retrieved {len(reg_citations)} governing standards: {', '.join([r['title'] for r in reg_citations])}."
        )
        yield {"event": "agent_thought", "data": t4.model_dump()}
        await asyncio.sleep(0.5)

        # Step 5: Synthesis
        detected_typologies = list(set([a.rule_name for a in anomalies]))
        if sanctioned_found:
            detected_typologies.append("OFAC Sanctions Evasion")

        flagged_tx_ids = set()
        for a in anomalies:
            flagged_tx_ids.update(a.transactions_involved)
        suspicious_txs = [t for t in transactions if t.id in flagged_tx_ids or len(t.risk_flags) > 0]
        total_susp_amt = sum(t.amount for t in suspicious_txs) if suspicious_txs else sum(t.amount for t in transactions)

        dossier = {
            "primary_suspects": [primary_suspect] + [e for e in all_suspect_entities if e != primary_suspect],
            "sanctions_hits": [screening_results[k] for k in sanctioned_found],
            "pep_hits": [screening_results[k] for k in pep_found],
            "typologies": detected_typologies,
            "regulations": reg_citations,
            "total_suspicious_volume": total_susp_amt,
            "flagged_transaction_count": len(suspicious_txs)
        }

        t5 = AgentThought(
            agent_name="Forensic Investigator Agent",
            step=5,
            action="SYNTHESIS_AND_CONCLUSION",
            thought="Aggregating all tool outputs to establish predicate offense and transfer dossier to SAR Drafter Agent.",
            observation=f"Synthesis complete. Verified {len(detected_typologies)} typologies totaling ${total_susp_amt:,.2f}."
        )
        yield {"event": "agent_thought", "data": t5.model_dump()}
        await asyncio.sleep(0.5)

        # Stage 3: Autonomous SAR Drafter
        sar_thought, sar_draft = await self.sar_drafter_agent.draft_sar(
            dossier=dossier,
            transactions=transactions,
            scenario_name=scenario_name
        )
        yield {"event": "agent_thought", "data": sar_thought.model_dump()}
        await asyncio.sleep(0.4)

        # Stage 4: Graph Data Generation
        sanctioned_entities = set([s["matched_name"] for s in dossier.get("sanctions_hits", []) if s.get("matched_name")])
        pep_entities = set([p["matched_name"] for p in dossier.get("pep_hits", []) if p.get("matched_name")])

        _, graph_data = self.graph_engine.build_graph(
            transactions=transactions,
            flagged_tx_ids=flagged_tx_ids,
            sanctioned_entities=sanctioned_entities,
            pep_entities=pep_entities
        )

        final_result = InvestigationResult(
            investigation_id=investigation_id,
            scenario_name=scenario_name,
            total_transactions=len(transactions),
            flagged_transactions_count=len(suspicious_txs),
            high_risk_entities_count=len(dossier["primary_suspects"]),
            anomalies=anomalies,
            agent_trace=[t1, t2, t3, t4, t5, sar_thought],
            sar_draft=sar_draft,
            graph_data=graph_data
        )

        yield {
            "event": "complete",
            "data": final_result.model_dump()
        }
