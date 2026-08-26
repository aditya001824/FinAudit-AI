"""
Regulatory RAG (Retrieval-Augmented Generation) Knowledge Base
Supplies legal standards, FATF 40 recommendations, and FinCEN SAR filing triggers.
"""
from typing import List, Dict, Any
import re

REGULATORY_CORPUS = [
    {
        "id": "FINCEN-BSA-STRUCTURING",
        "title": "FinCEN Bank Secrecy Act - Anti-Structuring Rule (31 CFR § 1010.314)",
        "typology": "Structuring / Smurfing",
        "legal_citation": "31 U.S.C. § 5324 / 31 CFR § 1010.314",
        "filing_threshold": "Totaling $5,000+ when conducted to evade CTR ($10,000)",
        "summary": "Prohibits any person from causing or attempting to cause a financial institution to fail to file a Currency Transaction Report (CTR), or structuring transactions to evade reporting requirements. Mandatory SAR filing required within 30 calendar days.",
        "keywords": ["structuring", "smurfing", "threshold", "ctr", "cash deposit", "sub-threshold", "9000", "9900", "multiple deposits"]
    },
    {
        "id": "FATF-REC-16-WIRE-TRANSIT",
        "title": "FATF Recommendation 16 - Wire Transfers & Pass-Through Layering",
        "typology": "Pass-Through / Rapid Layering",
        "legal_citation": "FATF 40 Recommendations (Rec. 16) / BSA Travel Rule 31 CFR § 1010.410(e)",
        "filing_threshold": "Cross-border wires exceeding $3,000 or suspicious rapid pass-through",
        "summary": "Mandates ordering financial institutions to transmit verified originator and beneficiary info. Accounts exhibiting rapid in-and-out pass-through with minimal balance retention (transit nodes) represent classic money laundering layering typologies requiring enhanced due diligence (EDD) and SAR filing.",
        "keywords": ["pass-through", "transit", "velocity", "wire", "layering", "rapid movement", "retention", "conduit"]
    },
    {
        "id": "OFAC-IEEPA-SANCTIONS",
        "title": "International Emergency Economic Powers Act (IEEPA) & OFAC Sanctions Screening",
        "typology": "Sanctions & High-Risk Corridors",
        "legal_citation": "50 U.S.C. § 1701-1707 / 31 CFR Chapter V",
        "filing_threshold": "Zero-dollar threshold for designated entities (Strict Liability)",
        "summary": "Requires immediate freezing of assets and blocking of transactions involving Specially Designated Nationals (SDNs), blocked jurisdictions (e.g. Russia, DPRK, Iran, Syria), or persons acting on their behalf. Blocking report must be submitted to OFAC within 10 business days, alongside FinCEN SAR.",
        "keywords": ["sanctions", "ofac", "sdn", "blocked", "embargo", "russia", "dprk", "north korea", "iran", "syria", "high-risk", "jurisdiction"]
    },
    {
        "id": "FINCEN-ADVISORY-TBML",
        "title": "FinCEN Advisory on Trade-Based Money Laundering (FIN-2010-A001)",
        "typology": "Trade-Based Money Laundering (TBML)",
        "legal_citation": "FinCEN Advisory FIN-2010-A001 / FATF TBML Best Practices",
        "filing_threshold": "Suspicious commercial invoices or discrepancies of $5,000+",
        "summary": "Trade-based money laundering involves the exploitation of international trade transactions to legitimize illicit proceeds. Indicators include over/under-invoicing of goods, phantom shipments, circular trade contracts, and vague service descriptions (e.g. consulting, management fees) paid via offshore intermediaries.",
        "keywords": ["trade", "invoice", "over-invoicing", "under-invoicing", "shipping", "consulting fee", "customs", "tbml", "goods", "import", "export"]
    },
    {
        "id": "FATF-REC-20-SAR-MANDATE",
        "title": "FATF Recommendation 20 - Suspicious Transaction Reporting & Form 111 Standards",
        "typology": "General Suspicious Activity",
        "legal_citation": "FATF Rec. 20 / FinCEN Form 111 (SAR-DI)",
        "filing_threshold": "Transactions having no apparent business or lawful purpose",
        "summary": "If a financial institution suspects or has reasonable grounds to suspect that funds are the proceeds of a criminal activity, it must file a Suspicious Activity Report (SAR). The narrative must clearly articulate the 5 W's and H (Who, What, Where, When, Why, How) with chronological transaction logs.",
        "keywords": ["sar", "suspicious activity", "narrative", "reporting", "fincen form 111", "bsa", "criminal proceeds", "compliance"]
    },
    {
        "id": "FINCEN-CYBER-CRYPTO-MIXER",
        "title": "FinCEN Guidance on Application of BSA Regulations to Virtual Assets (FIN-2019-G001)",
        "typology": "Crypto-Fiat Off-Ramp & Mixing",
        "legal_citation": "FinCEN Guidance FIN-2019-G001 / Section 311 USA PATRIOT Act",
        "filing_threshold": "Convertible Virtual Currency (CVC) mixing or unhosted wallet laundering",
        "summary": "Entities engaging in anonymizing services, mixers, peer-to-peer off-ramps, and unhosted wallet hops without KYC violate money transmission registration rules and represent acute AML risks requiring proactive blocking and SAR documentation.",
        "keywords": ["crypto", "mixer", "mixing", "unhosted", "virtual currency", "off-ramp", "peer-to-peer", "swap", "blockchain", "tumbler"]
    }
]


class RegulatoryRAG:
    def __init__(self):
        self.corpus = REGULATORY_CORPUS

    def retrieve_relevant_regulations(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant regulatory standards, legal citations, and filing guidance based on query.
        """
        query_words = set(re.findall(r'\w+', query.lower()))
        scored_docs = []

        for doc in self.corpus:
            doc_text = f"{doc['title']} {doc['typology']} {doc['summary']} {' '.join(doc['keywords'])}".lower()
            doc_words = set(re.findall(r'\w+', doc_text))
            
            # Compute keyword overlap & keyword list matching
            overlap = len(query_words.intersection(doc_words))
            keyword_hits = sum(1 for kw in doc["keywords"] if kw in query.lower())
            
            total_score = overlap + (keyword_hits * 3)
            
            if total_score > 0:
                scored_docs.append((total_score, doc))

        # Sort by relevance score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k results
        if not scored_docs:
            # Fallback to general SAR guidance
            return [self.corpus[4]]
        
        return [doc for score, doc in scored_docs[:top_k]]
