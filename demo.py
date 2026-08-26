"""
FinAudit AI - Interactive Terminal Demonstration
Runs a complete multi-agent forensic investigation and prints live reasoning steps & SAR filing.
"""
import sys
import asyncio
import json

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from backend.scenarios.scenario_loader import ScenarioLoader
from backend.agents.orchestrator import AMLOrchestrator

async def run_live_demo(scenario_id: str = "sanctions_evasion"):
    print("=" * 80)
    print("FINAUDIT AI — AUTONOMOUS AML MULTI-AGENT SWARM DEMO")
    print("=" * 80)

    # 1. Load Scenario
    scenario = ScenarioLoader.get_scenario(scenario_id)
    txs = ScenarioLoader.load_scenario_transactions(scenario_id)

    print(f"\n[+] SCENARIO: {scenario['name']}")
    print(f"[+] SEVERITY: {scenario['severity']}")
    print(f"[+] DESCRIPTION: {scenario['description']}")
    print(f"[+] INGESTED TRANSACTIONS: {len(txs)} records")
    print("-" * 80)

    for i, tx in enumerate(txs, 1):
        flags = f" [FLAGS: {', '.join(tx.risk_flags)}]" if tx.risk_flags else ""
        print(f"  [{i}] {tx.timestamp[:10]} | {tx.source_entity} ({tx.source_country}) --> [ ${tx.amount:,.2f} {tx.currency} ] --> {tx.target_entity} ({tx.target_country}){flags}")
    print("-" * 80)

    # 2. Initialize Swarm
    orchestrator = AMLOrchestrator()
    print("\n[+] LAUNCHING MULTI-AGENT REASONING PIPELINE (SSE STREAM)...")
    print("=" * 80)

    # 3. Stream Investigation Steps
    async for event in orchestrator.stream_investigation(transactions=txs, scenario_name=scenario['name']):
        etype = event.get("event")
        data = event.get("data", {})

        if etype == "start":
            print(f"\n[SYSTEM] Investigation Initialized (ID: {data['investigation_id']})")
        
        elif etype == "anomalies_detected":
            print(f"\n[ANOMALY DETECTOR ENGINE] Triggered {data['count']} Typological Alerts:")
            for a in data["anomalies"]:
                print(f"   * [{a['severity']}] {a['rule_name']} ({a['rule_id']})")
                print(f"     Description: {a['description']}")

        elif etype == "agent_thought":
            step = data.get("step")
            agent = data.get("agent_name")
            action = data.get("action")
            tool = data.get("tool")
            thought = data.get("thought")
            obs = data.get("observation")

            print(f"\n[AGENT STEP {step}] {agent} | ACTION: {action}")
            if tool:
                print(f"   >> TOOL EXECUTED: {tool}")
            print(f"   >> THOUGHT: \"{thought}\"")
            if obs:
                print(f"   >> OBSERVATION: {obs}")

        elif etype == "complete":
            sar = data.get("sar_draft", {})
            print("\n" + "=" * 80)
            print("OFFICIAL FINCEN FORM 111 — SUSPICIOUS ACTIVITY REPORT (SAR) GENERATED")
            print("=" * 80)
            print(f"SAR FILING ID:       {sar.get('sar_id')}")
            print(f"FILING INSTITUTION:  {sar.get('filing_institution')}")
            print(f"PRIMARY SUBJECT:     {sar.get('primary_subject')}")
            print(f"ASSOCIATED ENTITIES: {', '.join(sar.get('associated_entities', []))}")
            print(f"SUSPICIOUS AMOUNT:   ${sar.get('total_suspicious_amount', 0):,.2f} USD")
            print(f"ASSESSED RISK SCORE: {sar.get('overall_risk_score')} / 100")
            print(f"FILING STATUS:       {sar.get('status')}")
            
            print("\n" + "-" * 30 + " FORMAL SAR NARRATIVE " + "-" * 30)
            print(sar.get("narrative_summary", "").strip())
            
            print("\n" + "-" * 30 + " GOVERNING STATUTES CITED " + "-" * 30)
            for v in sar.get("regulatory_violations", []):
                print(f"  [LAW] {v}")

            print("\n" + "-" * 30 + " RECOMMENDED REMEDIATION ACTIONS " + "-" * 30)
            for act in sar.get("recommended_actions", []):
                print(f"  [ACTION] {act}")

            print("\n" + "=" * 80)
            print("DEMO COMPLETED SUCCESSFULLY — SAR DOSSIER COMPILED AND READY FOR SIGN-OFF.")
            print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_live_demo("sanctions_evasion"))
