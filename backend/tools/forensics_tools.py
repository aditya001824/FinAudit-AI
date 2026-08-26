"""
Forensic Financial Investigation Utilities & Tool Suite
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.models.transaction import Transaction

class ForensicsTools:
    def __init__(self):
        pass

    def build_entity_profile(self, entity_name: str, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Build an in-depth forensic profile for an entity across all known transactions.
        """
        inflow_tx = [t for t in transactions if t.target_entity.lower() == entity_name.lower()]
        outflow_tx = [t for t in transactions if t.source_entity.lower() == entity_name.lower()]

        total_in = sum(t.amount for t in inflow_tx)
        total_out = sum(t.amount for t in outflow_tx)
        
        counterparties_in = [t.source_entity for t in inflow_tx]
        counterparties_out = [t.target_entity for t in outflow_tx]
        unique_counterparties = list(set(counterparties_in + counterparties_out))

        countries_involved = list(set(
            [t.source_country for t in inflow_tx + outflow_tx] + 
            [t.target_country for t in inflow_tx + outflow_tx]
        ))

        all_tx_ids = [t.id for t in inflow_tx + outflow_tx]

        return {
            "entity_name": entity_name,
            "total_transactions": len(inflow_tx) + len(outflow_tx),
            "inflow_count": len(inflow_tx),
            "outflow_count": len(outflow_tx),
            "total_inflow_amount": total_in,
            "total_outflow_amount": total_out,
            "net_balance_change": total_in - total_out,
            "countries_involved": countries_involved,
            "unique_counterparties": unique_counterparties,
            "transaction_ids": all_tx_ids,
            "high_velocity_indicator": (total_in > 10000 and total_out > 10000 and abs(total_in - total_out) < (0.2 * total_in))
        }

    def construct_chronological_timeline(self, transactions: List[Transaction], entity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Construct a chronological sequence of transactions with forensic commentary.
        """
        txs = transactions
        if entity_filter:
            filt = entity_filter.lower()
            txs = [t for t in transactions if t.source_entity.lower() == filt or t.target_entity.lower() == filt]

        # Sort by timestamp
        sorted_tx = sorted(txs, key=lambda x: x.timestamp)
        
        timeline = []
        for tx in sorted_tx:
            timeline.append({
                "timestamp": tx.timestamp,
                "transaction_id": tx.id,
                "flow": f"{tx.source_entity} ({tx.source_country}) ──[ ${tx.amount:,.2f} {tx.currency} ]──► {tx.target_entity} ({tx.target_country})",
                "source": tx.source_entity,
                "target": tx.target_entity,
                "amount": tx.amount,
                "currency": tx.currency,
                "type": tx.transaction_type,
                "description": tx.description,
                "is_flagged": len(tx.risk_flags) > 0
            })
        return timeline

    def calculate_flow_of_funds(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Summarizes aggregate fund flows across the entire network.
        """
        total_volume = sum(t.amount for t in transactions)
        unique_senders = set(t.source_entity for t in transactions)
        unique_receivers = set(t.target_entity for t in transactions)
        
        return {
            "total_volume_usd": total_volume,
            "transaction_count": len(transactions),
            "unique_senders_count": len(unique_senders),
            "unique_receivers_count": len(unique_receivers),
            "unique_entities_total": len(unique_senders.union(unique_receivers))
        }
