"""
Autonomous AML Forensic Investigator Agent (ReAct Framework)
Executes tool calls, hypothesizes laundering patterns, and assembles structured evidence dossiers.
"""
from typing import List, Dict, Any, Tuple, Optional
import json
from backend.models.transaction import Transaction, AnomalyAlert, AgentThought
from backend.tools.sanctions_checker import SanctionsChecker
from backend.tools.regulatory_rag import RegulatoryRAG
from backend.tools.forensics_tools import ForensicsTools
from backend.agents.llm_client import LLMClient

class InvestigatorAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.sanctions_tool = SanctionsChecker()
        self.rag_tool = RegulatoryRAG()
        self.forensics_tool = ForensicsTools()

    async def investigate(
        self,
        transactions: List[Transaction],
        anomalies: List[AnomalyAlert],
        focus_entity: Optional[str] = None
    ) -> Tuple[List[AgentThought], Dict[str, Any]]:
        """
        Execute autonomous multi-step ReAct investigation.
        Returns the sequential agent thought trace and the compiled forensic evidence dossier.
        """
        thoughts: List[AgentThought] = []
        dossier: Dict[str, Any] = {
            "primary_suspects": [],
            "sanctions_hits": [],
            "pep_hits": [],
            "typologies": [],
            "regulations": [],
            "flow_summary": {},
            "total_suspicious_volume": 0.0,
            "evidence_items": []
        }

        # Step 1: Ingestion & Triage Hypothesis
        step = 1
        all_suspect_entities = list(set([e for a in anomalies for e in a.entities_involved]))
        if focus_entity and focus_entity not in all_suspect_entities:
            all_suspect_entities.append(focus_entity)

        hypothesis = (
            f"Detected {len(anomalies)} anomaly triggers across {len(all_suspect_entities)} key entities. "
            f"Initiating multi-vector forensic inquiry to test for structuring, circular wash routing, or sanctions evasion."
        )
        thoughts.append(AgentThought(
            agent_name="Forensic Investigator Agent",
            step=step,
            action="PLAN_AND_HYPOTHESIZE",
            thought="Reviewing initial anomaly flags to prioritize entities and establish investigation scope.",
            observation=hypothesis
        ))

        # Step 2: Sanctions & PEP Screening Tool
        step += 1
        screening_results = self.sanctions_tool.batch_screen(all_suspect_entities)
        sanctioned_found = [k for k, v in screening_results.items() if v.get("is_flagged") and v.get("list_type") == "SANCTIONS"]
        pep_found = [k for k, v in screening_results.items() if v.get("is_flagged") and v.get("list_type") == "PEP"]
        
        dossier["sanctions_hits"] = [screening_results[k] for k in sanctioned_found]
        dossier["pep_hits"] = [screening_results[k] for k in pep_found]

        thoughts.append(AgentThought(
            agent_name="Forensic Investigator Agent",
            step=step,
            action="EXECUTE_TOOL",
            tool="Sanctions & PEP Screening Tool",
            tool_input={"entities_screened": all_suspect_entities},
            tool_output={
                "sanctions_count": len(sanctioned_found),
                "pep_count": len(pep_found),
                "flagged_entities": sanctioned_found + pep_found
            },
            thought=f"Screening all {len(all_suspect_entities)} identified entities against OFAC SDN, UN Consolidated, EU Sanctions, and PEP databases.",
            observation=f"Screening completed: Found {len(sanctioned_found)} sanctioned entities ({', '.join(sanctioned_found) or 'None'}) and {len(pep_found)} PEPs ({', '.join(pep_found) or 'None'})."
        ))

        # Step 3: Transaction Timeline & Flow Analysis
        step += 1
        flow_summary = self.forensics_tool.calculate_flow_of_funds(transactions)
        dossier["flow_summary"] = flow_summary
        
        entity_profiles = {}
        for ent in all_suspect_entities:
            entity_profiles[ent] = self.forensics_tool.build_entity_profile(ent, transactions)

        # Identify primary suspect (highest volume / connectivity / flags)
        primary_suspect = all_suspect_entities[0] if all_suspect_entities else "Unknown Subject"
        if sanctioned_found:
            primary_suspect = sanctioned_found[0]
        elif len(all_suspect_entities) > 0:
            # Sort by total volume
            sorted_by_vol = sorted(all_suspect_entities, key=lambda e: entity_profiles.get(e, {}).get("total_inflow_amount", 0) + entity_profiles.get(e, {}).get("total_outflow_amount", 0), reverse=True)
            primary_suspect = sorted_by_vol[0]

        dossier["primary_suspects"] = [primary_suspect] + [e for e in all_suspect_entities if e != primary_suspect]
        dossier["entity_profiles"] = entity_profiles

        thoughts.append(AgentThought(
            agent_name="Forensic Investigator Agent",
            step=step,
            action="EXECUTE_TOOL",
            tool="Entity Profiler & Flow Reconstructor",
            tool_input={"primary_suspect": primary_suspect, "total_transactions": len(transactions)},
            tool_output={
                "primary_suspect": primary_suspect,
                "profile": entity_profiles.get(primary_suspect, {}),
                "total_network_volume": flow_summary["total_volume_usd"]
            },
            thought=f"Reconstructing flow-of-funds network and deep-profiling '{primary_suspect}' and related nodes.",
            observation=f"Primary suspect identified as '{primary_suspect}'. Inflow: ${entity_profiles.get(primary_suspect, {}).get('total_inflow_amount', 0):,.2f}, Outflow: ${entity_profiles.get(primary_suspect, {}).get('total_outflow_amount', 0):,.2f} across {len(entity_profiles.get(primary_suspect, {}).get('unique_counterparties', []))} counterparties."
        ))

        # Step 4: Regulatory RAG Query
        step += 1
        query_terms = " ".join([a.rule_name for a in anomalies]) + (" SANCTIONS OFAC" if sanctioned_found else "") + (" STRUCTURING" if any("Structuring" in a.rule_name for a in anomalies) else "")
        reg_citations = self.rag_tool.retrieve_relevant_regulations(query_terms, top_k=3)
        dossier["regulations"] = reg_citations

        thoughts.append(AgentThought(
            agent_name="Forensic Investigator Agent",
            step=step,
            action="EXECUTE_TOOL",
            tool="Regulatory RAG Knowledge Base",
            tool_input={"query": query_terms},
            tool_output={"retrieved_statutes": [r["id"] for r in reg_citations]},
            thought="Retrieving applicable BSA/FinCEN legal statutory authorities and filing guidelines for identified typologies.",
            observation=f"Retrieved {len(reg_citations)} governing standards: {', '.join([r['title'] for r in reg_citations])}."
        ))

        # Step 5: Forensic Synthesis & Typology Formalization
        step += 1
        detected_typologies = list(set([a.rule_name for a in anomalies]))
        if sanctioned_found:
            detected_typologies.append("OFAC Sanctions Evasion")
        if pep_found:
            detected_typologies.append("Politically Exposed Person (PEP) Corruption Risk")

        dossier["typologies"] = detected_typologies
        
        # Calculate suspicious volume
        flagged_tx_ids = set()
        for a in anomalies:
            flagged_tx_ids.update(a.transactions_involved)
        
        suspicious_txs = [t for t in transactions if t.id in flagged_tx_ids or len(t.risk_flags) > 0]
        total_susp_amt = sum(t.amount for t in suspicious_txs) if suspicious_txs else sum(t.amount for t in transactions)
        dossier["total_suspicious_volume"] = total_susp_amt
        dossier["flagged_transaction_count"] = len(suspicious_txs)

        synthesis_thought = (
            f"Investigation synthesized with high confidence. Total suspicious volume: ${total_susp_amt:,.2f}. "
            f"Confirmed {len(detected_typologies)} distinct AML typologies: {', '.join(detected_typologies)}. "
            f"Proceeding to Autonomous SAR Drafter Agent for formal regulatory document compilation."
        )

        thoughts.append(AgentThought(
            agent_name="Forensic Investigator Agent",
            step=step,
            action="SYNTHESIS_AND_CONCLUSION",
            thought="Evaluating total weight of evidence, establishing criminal nexus, and preparing handoff to SAR Drafter Agent.",
            observation=synthesis_thought
        ))

        return thoughts, dossier
