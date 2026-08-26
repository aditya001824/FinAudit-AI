"""
Curated Real-World Financial Crime Datasets & Scenarios
"""
from typing import List, Dict, Any
from backend.models.transaction import Transaction

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "structuring_ring": {
        "id": "structuring_ring",
        "name": "Smurfing & Structuring Network (Offshore Funnel)",
        "category": "Structuring & Smurfing",
        "severity": "HIGH",
        "description": "Six coordinated smurf individuals make sub-$10,000 cash deposits in rapid succession, funneled into an intermediary transit account before immediate wire transfer to a Cayman Islands shell company.",
        "transactions": [
            {
                "id": "TX-SMURF-101",
                "timestamp": "2026-08-20T09:15:00Z",
                "source_account": "ACC-90112",
                "target_account": "ACC-55201",
                "source_entity": "David Miller",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 9500.0,
                "currency": "USD",
                "transaction_type": "CASH_DEPOSIT",
                "source_country": "US",
                "target_country": "US",
                "description": "Branch cash deposit - teller 4",
                "risk_flags": ["SUB_CTR_THRESHOLD"]
            },
            {
                "id": "TX-SMURF-102",
                "timestamp": "2026-08-20T10:30:00Z",
                "source_account": "ACC-90113",
                "target_account": "ACC-55201",
                "source_entity": "Elena Rostova",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 9800.0,
                "currency": "USD",
                "transaction_type": "CASH_DEPOSIT",
                "source_country": "US",
                "target_country": "US",
                "description": "Branch cash deposit - teller 2",
                "risk_flags": ["SUB_CTR_THRESHOLD"]
            },
            {
                "id": "TX-SMURF-103",
                "timestamp": "2026-08-20T11:45:00Z",
                "source_account": "ACC-90114",
                "target_account": "ACC-55201",
                "source_entity": "Marcus Vance Jr.",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 9200.0,
                "currency": "USD",
                "transaction_type": "CASH_DEPOSIT",
                "source_country": "US",
                "target_country": "US",
                "description": "ATM cash deposit bundle",
                "risk_flags": ["SUB_CTR_THRESHOLD"]
            },
            {
                "id": "TX-SMURF-104",
                "timestamp": "2026-08-20T13:10:00Z",
                "source_account": "ACC-90115",
                "target_account": "ACC-55201",
                "source_entity": "Sarah Jenkins",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 9750.0,
                "currency": "USD",
                "transaction_type": "CASH_DEPOSIT",
                "source_country": "US",
                "target_country": "US",
                "description": "Branch cash deposit - teller 6",
                "risk_flags": ["SUB_CTR_THRESHOLD"]
            },
            {
                "id": "TX-SMURF-105",
                "timestamp": "2026-08-20T14:20:00Z",
                "source_account": "ACC-90116",
                "target_account": "ACC-55201",
                "source_entity": "Carlos Morales",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 8900.0,
                "currency": "USD",
                "transaction_type": "CASH_DEPOSIT",
                "source_country": "US",
                "target_country": "US",
                "description": "Over-the-counter deposit",
                "risk_flags": ["SUB_CTR_THRESHOLD"]
            },
            {
                "id": "TX-SMURF-106",
                "timestamp": "2026-08-21T08:00:00Z",
                "source_account": "ACC-55201",
                "target_account": "ACC-77881",
                "source_entity": "Apex Horizon Holdings LLC",
                "target_entity": "Aura Offshore Capital Ltd",
                "amount": 46500.0,
                "currency": "USD",
                "transaction_type": "WIRE",
                "source_country": "US",
                "target_country": "KY",
                "description": "International wire - Offshore fiduciary investment",
                "risk_flags": ["HIGH_VELOCITY_OUTFLOW", "OFFSHORE_HAVEN"]
            }
        ]
    },
    "sanctions_evasion": {
        "id": "sanctions_evasion",
        "name": "Sanctions Evasion & Dual-Layer Front Shell",
        "category": "OFAC Sanctions & Geopolitical Evasion",
        "severity": "CRITICAL",
        "description": "OFAC-sanctioned Russian energy firm routes large payments through a Cypriot maritime logistics front company to bypass correspondent banking sanctions filters.",
        "transactions": [
            {
                "id": "TX-SANC-201",
                "timestamp": "2026-08-22T08:30:00Z",
                "source_account": "ACC-RU-0019",
                "target_account": "ACC-CY-4412",
                "source_entity": "Volkov Energy Trading LLC",
                "target_entity": "Helios Maritime Logistics Ltd",
                "amount": 350000.0,
                "currency": "USD",
                "transaction_type": "WIRE",
                "source_country": "RU",
                "target_country": "CY",
                "description": "Bunker fuel and marine transport charter fee",
                "risk_flags": ["SANCTIONED_ORIGIN", "HIGH_RISK_JURISDICTION"]
            },
            {
                "id": "TX-SANC-202",
                "timestamp": "2026-08-22T14:15:00Z",
                "source_account": "ACC-CY-4412",
                "target_account": "ACC-US-8891",
                "source_entity": "Helios Maritime Logistics Ltd",
                "target_entity": "Vanguard Atlantic Holdings",
                "amount": 345000.0,
                "currency": "USD",
                "transaction_type": "WIRE",
                "source_country": "CY",
                "target_country": "US",
                "description": "Commercial supply chain settlement invoice #4491",
                "risk_flags": ["RAPID_TRANSIT_PASS_THROUGH"]
            },
            {
                "id": "TX-SANC-203",
                "timestamp": "2026-08-23T09:00:00Z",
                "source_account": "ACC-US-8891",
                "target_account": "ACC-VG-1002",
                "source_entity": "Vanguard Atlantic Holdings",
                "target_entity": "Aura Offshore Capital Ltd",
                "amount": 330000.0,
                "currency": "USD",
                "transaction_type": "SHELL_TRANSFER",
                "source_country": "US",
                "target_country": "VG",
                "description": "Intercompany loan repayment - Tortola trust",
                "risk_flags": ["OFFSHORE_SECRECY"]
            }
        ]
    },
    "trade_based_ml": {
        "id": "trade_based_ml",
        "name": "Trade-Based Money Laundering (TBML) & Wash Cycle",
        "category": "Trade Over-Invoicing & Round-Tripping",
        "severity": "HIGH",
        "description": "Circular round-trip wash trade where entities execute high-value phantom software and advisory invoices in a complete loop (A -> B -> C -> A) to disguise origin.",
        "transactions": [
            {
                "id": "TX-TBML-301",
                "timestamp": "2026-08-24T09:00:00Z",
                "source_account": "ACC-US-501",
                "target_account": "ACC-PA-802",
                "source_entity": "Northstar Global Imports",
                "target_entity": "Pacific Commodities Corp",
                "amount": 185000.0,
                "currency": "USD",
                "transaction_type": "TRADE_INVOICE",
                "source_country": "US",
                "target_country": "PA",
                "description": "CONSULTING FEE for Latin America distribution rights",
                "risk_flags": ["TBML_INDICATOR", "HIGH_RISK_JURISDICTION"]
            },
            {
                "id": "TX-TBML-302",
                "timestamp": "2026-08-24T12:30:00Z",
                "source_account": "ACC-PA-802",
                "target_account": "ACC-CH-903",
                "source_entity": "Pacific Commodities Corp",
                "target_entity": "Alpine Tech Management AG",
                "amount": 182000.0,
                "currency": "USD",
                "transaction_type": "TRADE_INVOICE",
                "source_country": "PA",
                "target_country": "CH",
                "description": "SOFTWARE LICENSE for automated commodity arbitrage",
                "risk_flags": ["TBML_INDICATOR"]
            },
            {
                "id": "TX-TBML-303",
                "timestamp": "2026-08-24T16:00:00Z",
                "source_account": "ACC-CH-903",
                "target_account": "ACC-US-501",
                "source_entity": "Alpine Tech Management AG",
                "target_entity": "Northstar Global Imports",
                "amount": 180000.0,
                "currency": "USD",
                "transaction_type": "WIRE",
                "source_country": "CH",
                "target_country": "US",
                "description": "ADVISORY rebate & marketing co-op fee",
                "risk_flags": ["CIRCULAR_WASH_RETURN"]
            }
        ]
    },
    "crypto_offramp": {
        "id": "crypto_offramp",
        "name": "Crypto Mixer & High-Velocity Fiat Off-Ramp",
        "category": "Virtual Asset Laundering & P2P Tumbling",
        "severity": "CRITICAL",
        "description": "Unlicensed peer-to-peer cryptocurrency mixing platform disperses high-velocity fiat proceeds across domestic accounts that immediately purchase commercial real estate escrow.",
        "transactions": [
            {
                "id": "TX-CRYPTO-401",
                "timestamp": "2026-08-25T11:00:00Z",
                "source_account": "ACC-VU-772",
                "target_account": "ACC-US-331",
                "source_entity": "SilkRoad Peer2Peer Swap",
                "target_entity": "Apex Horizon Holdings LLC",
                "amount": 125000.0,
                "currency": "USD",
                "transaction_type": "CRYPTO_SWAP",
                "source_country": "VU",
                "target_country": "US",
                "description": "P2P virtual currency liquidity settlement",
                "risk_flags": ["UNREGISTERED_MIXER", "HIGH_RISK_ORIGIN"]
            },
            {
                "id": "TX-CRYPTO-402",
                "timestamp": "2026-08-25T11:05:00Z",
                "source_account": "ACC-VU-772",
                "target_account": "ACC-US-332",
                "source_entity": "SilkRoad Peer2Peer Swap",
                "target_entity": "David Miller",
                "amount": 75000.0,
                "currency": "USD",
                "transaction_type": "CRYPTO_SWAP",
                "source_country": "VU",
                "target_country": "US",
                "description": "P2P escrow payout",
                "risk_flags": ["UNREGISTERED_MIXER"]
            },
            {
                "id": "TX-CRYPTO-403",
                "timestamp": "2026-08-25T15:30:00Z",
                "source_account": "ACC-US-331",
                "target_account": "ACC-US-TITLE-01",
                "source_entity": "Apex Horizon Holdings LLC",
                "target_entity": "Metropolitan Title & Escrow Corp",
                "amount": 195000.0,
                "currency": "USD",
                "transaction_type": "WIRE",
                "source_country": "US",
                "target_country": "US",
                "description": "Earnest deposit for commercial property acquisition",
                "risk_flags": ["REAL_ESTATE_INTEGRATION"]
            }
        ]
    }
}


class ScenarioLoader:
    @staticmethod
    def get_all_scenarios_metadata() -> List[Dict[str, Any]]:
        """List summary of all available scenarios."""
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "category": s["category"],
                "severity": s["severity"],
                "description": s["description"],
                "transaction_count": len(s["transactions"])
            }
            for s in SCENARIOS.values()
        ]

    @staticmethod
    def load_scenario_transactions(scenario_id: str) -> List[Transaction]:
        """Load transactions for a specific scenario."""
        sc = SCENARIOS.get(scenario_id)
        if not sc:
            raise ValueError(f"Scenario '{scenario_id}' not found.")
        return [Transaction(**t) for t in sc["transactions"]]

    @staticmethod
    def get_scenario(scenario_id: str) -> Dict[str, Any]:
        sc = SCENARIOS.get(scenario_id)
        if not sc:
            raise ValueError(f"Scenario '{scenario_id}' not found.")
        return sc
