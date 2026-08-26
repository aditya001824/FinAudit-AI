"""
Forensic Anomaly Detection Engine for AML & Financial Crimes
"""
from typing import List, Dict, Any, Set
from collections import defaultdict
from datetime import datetime
from backend.models.transaction import Transaction, AnomalyAlert

# High risk jurisdictions (FATF blacklist/greylist & offshore secrecy jurisdictions)
HIGH_RISK_JURISDICTIONS = {
    "KP": "North Korea (FATF Blacklist)",
    "IR": "Iran (FATF Blacklist)",
    "MM": "Myanmar (FATF Blacklist)",
    "RU": "Russian Federation (Sanctions / High Risk)",
    "SY": "Syria (Sanctions / High Risk)",
    "KY": "Cayman Islands (High-Secrecy Offshore)",
    "VG": "British Virgin Islands (High-Secrecy Offshore)",
    "PA": "Panama (Offshore Secrecy & Tax Haven)",
    "SC": "Seychelles (Offshore Haven)",
    "BZ": "Belize (Offshore Haven)",
    "CY": "Cyprus (High Risk Financial Gateway)",
    "VU": "Vanuatu (Offshore Crypto / Fin Haven)",
}

CTR_THRESHOLD = 10000.0
STRUCTURING_LOWER_BOUND = 7500.0
STRUCTURING_UPPER_BOUND = 9999.0


class AnomalyDetector:
    def __init__(self):
        pass

    def analyze_transactions(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Run full heuristic and topological anomaly suite across transaction stream.
        """
        alerts: List[AnomalyAlert] = []
        
        alerts.extend(self._detect_structuring(transactions))
        alerts.extend(self._detect_velocity_and_pass_through(transactions))
        alerts.extend(self._detect_high_risk_jurisdictions(transactions))
        alerts.extend(self._detect_aggregation_and_dispersion(transactions))
        alerts.extend(self._detect_round_trip_circular(transactions))
        alerts.extend(self._detect_abnormal_trade_invoices(transactions))

        return alerts

    def _detect_structuring(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects Smurfing / Structuring: repeated transactions just below the $10,000 threshold.
        """
        alerts = []
        entity_sub_threshold_tx: Dict[str, List[Transaction]] = defaultdict(list)

        for tx in transactions:
            if STRUCTURING_LOWER_BOUND <= tx.amount <= STRUCTURING_UPPER_BOUND:
                entity_sub_threshold_tx[tx.source_entity].append(tx)
                if tx.source_entity != tx.target_entity:
                    entity_sub_threshold_tx[tx.target_entity].append(tx)

        for entity, tx_list in entity_sub_threshold_tx.items():
            if len(tx_list) >= 2:
                total_vol = sum(t.amount for t in tx_list)
                tx_ids = [t.id for t in tx_list]
                alerts.append(
                    AnomalyAlert(
                        rule_id="AML-TYP-001",
                        rule_name="Suspected Structuring / Smurfing Pattern",
                        severity="CRITICAL" if len(tx_list) >= 3 else "HIGH",
                        description=f"Entity '{entity}' conducted {len(tx_list)} structured transactions just below the ${CTR_THRESHOLD:,.0f} reporting threshold totaling ${total_vol:,.2f}.",
                        entities_involved=[entity],
                        transactions_involved=tx_ids,
                        evidence={
                            "sub_threshold_count": len(tx_list),
                            "total_structured_amount": total_vol,
                            "average_amount": total_vol / len(tx_list),
                            "threshold_avoided": CTR_THRESHOLD
                        },
                        confidence=0.92
                    )
                )
        return alerts

    def _detect_velocity_and_pass_through(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects rapid pass-through of funds (Layering): Inflow followed almost immediately by outflow.
        """
        alerts = []
        inflows: Dict[str, List[Transaction]] = defaultdict(list)
        outflows: Dict[str, List[Transaction]] = defaultdict(list)

        for tx in transactions:
            outflows[tx.source_entity].append(tx)
            inflows[tx.target_entity].append(tx)

        # Look for entities with high symmetric inflow and outflow
        all_entities = set(inflows.keys()).intersection(set(outflows.keys()))
        for entity in all_entities:
            in_sum = sum(t.amount for t in inflows[entity])
            out_sum = sum(t.amount for t in outflows[entity])
            
            # Pass through ratio
            if in_sum > 20000 and out_sum > 20000:
                diff = abs(in_sum - out_sum)
                ratio = diff / max(in_sum, out_sum)
                # If inflow and outflow match within 15% (classic transit account)
                if ratio < 0.15:
                    tx_ids = list(set([t.id for t in inflows[entity] + outflows[entity]]))
                    alerts.append(
                        AnomalyAlert(
                            rule_id="AML-TYP-002",
                            rule_name="Pass-Through / Transit Account Layering",
                            severity="HIGH",
                            description=f"Entity '{entity}' acted as a rapid conduit/transit node with symmetric fund pass-through (Inflow: ${in_sum:,.2f}, Outflow: ${out_sum:,.2f}, Retention: {ratio*100:.1f}%).",
                            entities_involved=[entity],
                            transactions_involved=tx_ids,
                            evidence={
                                "inflow_total": in_sum,
                                "outflow_total": out_sum,
                                "variance_pct": round(ratio * 100, 2),
                                "retained_balance": diff
                            },
                            confidence=0.88
                        )
                    )
        return alerts

    def _detect_high_risk_jurisdictions(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects transfers to/from high-risk, non-cooperative, or heavily sanctioned jurisdictions.
        """
        alerts = []
        for tx in transactions:
            src_risk = HIGH_RISK_JURISDICTIONS.get(tx.source_country.upper())
            tgt_risk = HIGH_RISK_JURISDICTIONS.get(tx.target_country.upper())

            if src_risk or tgt_risk:
                risk_info = src_risk if src_risk else tgt_risk
                country_code = tx.source_country if src_risk else tx.target_country
                is_blacklist = "Blacklist" in risk_info or "Sanctions" in risk_info
                
                alerts.append(
                    AnomalyAlert(
                        rule_id="AML-TYP-003",
                        rule_name="High-Risk & Sanctioned Corridor Transfer",
                        severity="CRITICAL" if is_blacklist else "HIGH",
                        description=f"Transaction {tx.id} (${tx.amount:,.2f}) transacted across high-risk jurisdiction {country_code} ({risk_info}).",
                        entities_involved=[tx.source_entity, tx.target_entity],
                        transactions_involved=[tx.id],
                        evidence={
                            "jurisdiction": country_code,
                            "jurisdiction_classification": risk_info,
                            "amount": tx.amount,
                            "direction": f"{tx.source_country} -> {tx.target_country}"
                        },
                        confidence=0.95
                    )
                )
        return alerts

    def _detect_aggregation_and_dispersion(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects Fan-In (Aggregation: many sources -> 1 collector) and Fan-Out (Dispersion: 1 source -> many targets).
        """
        alerts = []
        senders_per_target: Dict[str, Set[str]] = defaultdict(set)
        receivers_per_source: Dict[str, Set[str]] = defaultdict(set)
        tx_by_target: Dict[str, List[Transaction]] = defaultdict(list)
        tx_by_source: Dict[str, List[Transaction]] = defaultdict(list)

        for tx in transactions:
            senders_per_target[tx.target_entity].add(tx.source_entity)
            receivers_per_source[tx.source_entity].add(tx.target_entity)
            tx_by_target[tx.target_entity].append(tx)
            tx_by_source[tx.source_entity].append(tx)

        # Fan-in (U-Turn / Funnel)
        for target, senders in senders_per_target.items():
            if len(senders) >= 3:
                total_inflow = sum(t.amount for t in tx_by_target[target])
                alerts.append(
                    AnomalyAlert(
                        rule_id="AML-TYP-004",
                        rule_name="Fan-In Funnel / Fund Aggregation Hub",
                        severity="HIGH",
                        description=f"Entity '{target}' aggregated funds from {len(senders)} distinct sender entities totaling ${total_inflow:,.2f}.",
                        entities_involved=[target] + list(senders),
                        transactions_involved=[t.id for t in tx_by_target[target]],
                        evidence={
                            "unique_senders_count": len(senders),
                            "senders_list": list(senders),
                            "total_aggregated_amount": total_inflow
                        },
                        confidence=0.89
                    )
                )

        # Fan-out (Dispersion)
        for source, receivers in receivers_per_source.items():
            if len(receivers) >= 3:
                total_outflow = sum(t.amount for t in tx_by_source[source])
                alerts.append(
                    AnomalyAlert(
                        rule_id="AML-TYP-005",
                        rule_name="Fan-Out Dispersion / Smurf Distribution",
                        severity="HIGH",
                        description=f"Entity '{source}' dispersed funds across {len(receivers)} distinct recipient entities totaling ${total_outflow:,.2f}.",
                        entities_involved=[source] + list(receivers),
                        transactions_involved=[t.id for t in tx_by_source[source]],
                        evidence={
                            "unique_recipients_count": len(receivers),
                            "recipients_list": list(receivers),
                            "total_dispersed_amount": total_outflow
                        },
                        confidence=0.87
                    )
                )

        return alerts

    def _detect_round_trip_circular(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects circular round-tripping: A -> B -> C -> A.
        """
        import networkx as nx
        alerts = []
        G = nx.DiGraph()

        for tx in transactions:
            G.add_edge(tx.source_entity, tx.target_entity, tx_id=tx.id, amount=tx.amount)

        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if len(cycle) >= 2:
                    cycle_nodes = list(cycle)
                    cycle_tx_ids = []
                    for i in range(len(cycle_nodes)):
                        u = cycle_nodes[i]
                        v = cycle_nodes[(i + 1) % len(cycle_nodes)]
                        edge_data = G.get_edge_data(u, v)
                        if edge_data and "tx_id" in edge_data:
                            cycle_tx_ids.append(edge_data["tx_id"])

                    cycle_str = " -> ".join(cycle_nodes + [cycle_nodes[0]])
                    alerts.append(
                        AnomalyAlert(
                            rule_id="AML-TYP-006",
                            rule_name="Circular Round-Tripping Wash Trade",
                            severity="CRITICAL",
                            description=f"Circular fund flow detected: {cycle_str}. Funds returned to source network with no genuine economic rationale.",
                            entities_involved=cycle_nodes,
                            transactions_involved=cycle_tx_ids,
                            evidence={
                                "cycle_path": cycle_nodes,
                                "cycle_length": len(cycle_nodes),
                                "flow": cycle_str
                            },
                            confidence=0.96
                        )
                    )
        except Exception:
            pass

        return alerts

    def _detect_abnormal_trade_invoices(self, transactions: List[Transaction]) -> List[AnomalyAlert]:
        """
        Detects Trade-Based Money Laundering (TBML), phantom shipments, and over-invoicing indicators.
        """
        alerts = []
        tbml_keywords = ["CONSULTING FEE", "SOFTWARE LICENSE", "MANAGEMENT FEE", "ADVISORY", "COMMODITY ESCROW", "EXPEDITE FEE"]
        
        for tx in transactions:
            desc_upper = tx.description.upper()
            is_tbml_desc = any(k in desc_upper for k in tbml_keywords)
            if (tx.amount > 100000.0 and is_tbml_desc) or tx.transaction_type == "TRADE_INVOICE":
                alerts.append(
                    AnomalyAlert(
                        rule_id="AML-TYP-007",
                        rule_name="Suspected Trade-Based ML / Opaque Invoice",
                        severity="MEDIUM" if tx.amount < 250000 else "HIGH",
                        description=f"High-value intangible trade invoice ({tx.id}) for ${tx.amount:,.2f} with description '{tx.description}' between {tx.source_entity} and {tx.target_entity}.",
                        entities_involved=[tx.source_entity, tx.target_entity],
                        transactions_involved=[tx.id],
                        evidence={
                            "invoice_memo": tx.description,
                            "amount": tx.amount,
                            "type": tx.transaction_type
                        },
                        confidence=0.82
                    )
                )
        return alerts
