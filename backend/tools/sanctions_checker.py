"""
Sanctions & PEP (Politically Exposed Persons) Screening Tool
Screens against simulated OFAC SDN, UN, EU Watchlists and PEP Registries.
"""
from typing import Dict, List, Any, Optional
import difflib

# Curated global watchlists & PEP database
WATCHLIST_DATABASE = [
    {
        "name": "Volkov Energy Trading LLC",
        "aliases": ["Volkov Group", "V-Energy Moscow", "Volkov Neft"],
        "program": "OFAC-SDN-RUSSIA-EO14024",
        "list_type": "SANCTIONS",
        "country": "RU",
        "reason": "Entity designated under Russian sectoral sanctions for evasion of oil price caps.",
        "risk_tier": "CRITICAL"
    },
    {
        "name": "Al-Nour Horizon Logistics Ltd",
        "aliases": ["Horizon Shipping Beirut", "Al-Nour Maritime", "Al Noor Logistics"],
        "program": "UN-SDGT-TERRORISM-RES1373",
        "list_type": "SANCTIONS",
        "country": "SY",
        "reason": "Front logistics company facilitating sanctioned dual-use hardware shipments.",
        "risk_tier": "CRITICAL"
    },
    {
        "name": "Pyongyang Quantum Trade Corp",
        "aliases": ["DPRK Quantum Tech", "Quantum Trade Pyongyang"],
        "program": "UN-DPRK-RES1718",
        "list_type": "SANCTIONS",
        "country": "KP",
        "reason": "Illicit DPRK cyber theft laundering and component procurement front.",
        "risk_tier": "CRITICAL"
    },
    {
        "name": "General Carlos Morales",
        "aliases": ["Carlos Alberto Morales-Vega", "Gen. C. Morales"],
        "program": "EU-HUMAN-RIGHTS-SANCTIONS",
        "list_type": "PEP",
        "country": "VE",
        "reason": "Senior government official involved in illicit state mining contracts.",
        "risk_tier": "HIGH"
    },
    {
        "name": "Senator Marcus Vance",
        "aliases": ["Marcus E. Vance", "M. Vance Trust"],
        "program": "FATF-PEP-DOMESTIC",
        "list_type": "PEP",
        "country": "US",
        "reason": "Domestic Politically Exposed Person (Chairman of Energy Oversight Committee).",
        "risk_tier": "HIGH"
    },
    {
        "name": "Aura Offshore Capital Ltd",
        "aliases": ["Aura Capital BVI", "Aura Holdings Tortola"],
        "program": "EU-HIGH-RISK-THIRD-COUNTRY",
        "list_type": "WATCHLIST",
        "country": "VG",
        "reason": "Unlicensed fiduciary shell identified in leaked paradise offshore registers.",
        "risk_tier": "HIGH"
    },
    {
        "name": "SilkRoad Peer2Peer Swap",
        "aliases": ["SilkSwap P2P", "SilkRoad Crypto Escrow"],
        "program": "FINCEN-ADVISORY-UNHOSTED-MIXER",
        "list_type": "SANCTIONS",
        "country": "VU",
        "reason": "Unregistered high-velocity cryptocurrency mixer and fiat off-ramp conduit.",
        "risk_tier": "CRITICAL"
    }
]


class SanctionsChecker:
    def __init__(self, match_threshold: float = 0.75):
        self.match_threshold = match_threshold
        self.database = WATCHLIST_DATABASE

    def screen_entity(self, entity_name: str) -> Dict[str, Any]:
        """
        Screen an entity against Sanctions and PEP database using fuzzy and token matching.
        """
        entity_clean = entity_name.strip().lower()
        best_match = None
        highest_score = 0.0

        for entry in self.database:
            all_names = [entry["name"].lower()] + [a.lower() for a in entry["aliases"]]
            for target_name in all_names:
                # 1. Exact match
                if entity_clean == target_name:
                    return {
                        "is_flagged": True,
                        "match_score": 1.0,
                        "matched_name": entry["name"],
                        "program": entry["program"],
                        "list_type": entry["list_type"],
                        "country": entry["country"],
                        "reason": entry["reason"],
                        "risk_tier": entry["risk_tier"],
                        "entity_queried": entity_name
                    }
                
                # 2. Token / Sequence Matcher
                score = difflib.SequenceMatcher(None, entity_clean, target_name).ratio()
                
                # Boost if key tokens match
                tokens_e = set(entity_clean.split())
                tokens_t = set(target_name.split())
                token_overlap = len(tokens_e.intersection(tokens_t))
                if token_overlap >= 2 and len(tokens_e) <= 4:
                    score = max(score, 0.85)

                if score > highest_score:
                    highest_score = score
                    best_match = entry

        if highest_score >= self.match_threshold and best_match:
            return {
                "is_flagged": True,
                "match_score": round(highest_score, 3),
                "matched_name": best_match["name"],
                "program": best_match["program"],
                "list_type": best_match["list_type"],
                "country": best_match["country"],
                "reason": best_match["reason"],
                "risk_tier": best_match["risk_tier"],
                "entity_queried": entity_name
            }

        return {
            "is_flagged": False,
            "match_score": round(highest_score, 3),
            "matched_name": None,
            "program": None,
            "list_type": None,
            "reason": "Clean - No matching records found on OFAC, UN, EU or PEP watchlists.",
            "risk_tier": "LOW",
            "entity_queried": entity_name
        }

    def batch_screen(self, entity_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Screen multiple entities in batch."""
        results = {}
        for name in entity_names:
            results[name] = self.screen_entity(name)
        return results
