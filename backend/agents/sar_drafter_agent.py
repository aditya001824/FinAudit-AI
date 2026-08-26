"""
Autonomous SAR (Suspicious Activity Report) Drafter Agent
Generates FinCEN Form 111-compliant compliance filings, executive narratives, and legal citations.
"""
from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime, timezone
from backend.models.transaction import Transaction, SARDraft, AgentThought
from backend.agents.llm_client import LLMClient
from backend.tools.forensics_tools import ForensicsTools

class SARDrafterAgent:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.forensics_tool = ForensicsTools()

    async def draft_sar(
        self,
        dossier: Dict[str, Any],
        transactions: List[Transaction],
        scenario_name: str = "Forensic Investigation"
    ) -> Tuple[AgentThought, SARDraft]:
        """
        Synthesize forensic dossier into a standardized FinCEN Form 111 SAR filing.
        """
        sar_id = f"SAR-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"
        primary_subject = dossier.get("primary_suspects", ["Unknown Subject"])[0] if dossier.get("primary_suspects") else "Unknown Subject"
        associated_entities = [e for e in dossier.get("primary_suspects", []) if e != primary_subject]
        
        total_amount = dossier.get("total_suspicious_volume", 0.0)
        typologies = dossier.get("typologies", ["Suspicious High-Velocity Movement"])
        regulations = dossier.get("regulations", [])
        sanctions_hits = dossier.get("sanctions_hits", [])
        pep_hits = dossier.get("pep_hits", [])

        # Build chronological timeline
        timeline = self.forensics_tool.construct_chronological_timeline(transactions)
        
        # Jurisdictions
        all_countries = list(set([t.source_country for t in transactions] + [t.target_country for t in transactions]))

        # Date range
        sorted_tx = sorted(transactions, key=lambda x: x.timestamp)
        date_range = f"{sorted_tx[0].timestamp[:10]} to {sorted_tx[-1].timestamp[:10]}" if sorted_tx else "N/A"

        # Calculate Risk Score (0-100)
        risk_score = 50.0
        if sanctions_hits:
            risk_score += 35.0
        if pep_hits:
            risk_score += 20.0
        if any("Structuring" in t for t in typologies):
            risk_score += 20.0
        if any("Circular" in t for t in typologies):
            risk_score += 25.0
        if any("Sanctions" in t or "High-Risk" in t for t in typologies):
            risk_score += 25.0
        risk_score = min(98.5, max(45.0, risk_score))

        # Generate Legal Citations string
        legal_citations = [f"{r['title']} ({r['legal_citation']})" for r in regulations]
        if not legal_citations:
            legal_citations = ["Bank Secrecy Act (31 U.S.C. § 5318(g))", "31 CFR § 1020.320"]

        # Formulate Suspicious Activity Narrative (FinCEN 5 W's & H)
        narrative_parts = []
        narrative_parts.append(f"### 1. EXECUTIVE SUMMARY\nFinAudit Sentinel Bank is filing this Suspicious Activity Report (SAR) regarding the financial transactions and network activities of primary subject '{primary_subject}' and affiliated counterparties ({', '.join(associated_entities) or 'N/A'}). During the review period from {date_range}, suspicious transactions totaling ${total_amount:,.2f} USD were executed across multiple jurisdictions ({', '.join(all_countries)}).\n")
        
        narrative_parts.append(f"### 2. SUBJECT & ENTITY BACKGROUND\nThe primary target '{primary_subject}' exhibited transaction behaviors inconsistent with legitimate commercial operations.")
        if sanctions_hits:
            sanction_details = "; ".join([f"{s['matched_name']} ({s['program']} - {s['reason']})" for s in sanctions_hits])
            narrative_parts.append(f"CRITICAL SANCTIONS ALERT: Entity matched against international sanctions watchlists: {sanction_details}.")
        if pep_hits:
            pep_details = "; ".join([f"{p['matched_name']} ({p['reason']})" for p in pep_hits])
            narrative_parts.append(f"PEP INVOLVEMENT: Subject is flagged as Politically Exposed Person: {pep_details}.")

        narrative_parts.append(f"\n### 3. TYPOLOGY & METHODOLOGY BREAKDOWN\nThe investigation confirmed the following money laundering mechanisms:\n" + "\n".join([f"- **{t}**" for t in typologies]))

        narrative_parts.append(f"\n### 4. CHRONOLOGICAL FLOW OF FUNDS & PATTERN OF ACTIVITY\nTransactional analysis revealed a structured pattern of movement:")
        for idx, event in enumerate(timeline[:8], 1):
            flag_marker = " [FLAGGED]" if event["is_flagged"] else ""
            narrative_parts.append(f"{idx}. **{event['timestamp']}**: {event['flow']} (Type: {event['type']}, Memo: '{event['description']}'){flag_marker}")
        if len(timeline) > 8:
            narrative_parts.append(f"... and {len(timeline) - 8} additional related structured transactions.")

        narrative_parts.append(f"\n### 5. REGULATORY BASIS & LEGAL STATUTES\nThis filing is mandated under the following statutory authorities:\n" + "\n".join([f"- {c}" for c in legal_citations]))

        narrative_parts.append(f"\n### 6. CONCLUSION & RECOMMENDATIONS\nBased on the totality of circumstances, the transaction patterns lack economic substance and indicate deliberate layering/structuring designed to obfuscate beneficial ownership.\n")

        full_narrative = "\n".join(narrative_parts)

        # Recommended Actions
        recommended_actions = [
            f"Restrict and freeze accounts associated with '{primary_subject}' pending law enforcement subpoena.",
            "Submit Form 111 electronic filing to Financial Crimes Enforcement Network (FinCEN).",
            "File immediate Blocking Report with U.S. Treasury Office of Foreign Assets Control (OFAC) if sanctions match is confirmed.",
            "Initiate counterparty review for downstream beneficiary financial institutions.",
            "Place all associated tax IDs and entity aliases on internal negative list / enhanced monitoring."
        ]

        sar_draft = SARDraft(
            sar_id=sar_id,
            filing_institution="FinAudit Sentinel AML Compliance Unit, N.A.",
            filing_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            primary_subject=primary_subject,
            associated_entities=associated_entities,
            total_suspicious_amount=round(total_amount, 2),
            currency="USD",
            typologies_identified=typologies,
            suspicious_date_range=date_range,
            jurisdictions_involved=all_countries,
            narrative_summary=full_narrative,
            chronological_timeline=timeline,
            regulatory_violations=legal_citations,
            recommended_actions=recommended_actions,
            overall_risk_score=round(risk_score, 1),
            confidence_score=0.94,
            status="DRAFT_PENDING_REVIEW"
        )

        thought = AgentThought(
            agent_name="Autonomous SAR Drafter Agent",
            step=6,
            action="GENERATE_SAR_FILING",
            tool="FinCEN Form 111 Legal Narrative Generator",
            tool_input={"sar_id": sar_id, "primary_subject": primary_subject, "total_amount": total_amount},
            tool_output={"status": "DRAFT_CREATED", "risk_score": risk_score, "violations_cited": len(legal_citations)},
            thought="Compiling complete FinCEN-compliant Suspicious Activity Report (SAR) with chronological narrative, legal authorities, and remediation action plan.",
            observation=f"SAR '{sar_id}' successfully generated for '{primary_subject}'. Assessed Risk Score: {risk_score}/100. Audit dossier ready for compliance officer sign-off."
        )

        return thought, sar_draft
