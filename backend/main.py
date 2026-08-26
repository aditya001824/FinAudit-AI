"""
FinAudit AI - FastAPI Application Server
Enterprise Multi-Agent AML Forensic Investigation System
"""
import os
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel

from backend.models.transaction import (
    Transaction,
    InvestigationRequest,
    InvestigationResult,
    SARDraft
)
from backend.agents.orchestrator import AMLOrchestrator
from backend.scenarios.scenario_loader import ScenarioLoader, SCENARIOS

app = FastAPI(
    title="FinAudit AI - Autonomous AML & Forensic Intelligence Swarm",
    description="Enterprise Multi-Agent System for Anti-Money Laundering, Sanctions Screening, and Automated SAR Generation.",
    version="1.0.0"
)

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for generated SAR reports and investigations
sar_repository: dict = {}
investigation_repository: dict = {}

orchestrator = AMLOrchestrator()


@app.get("/api/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "FinAudit AI Swarm",
        "version": "1.0.0",
        "llm_provider": orchestrator.llm_client.provider,
        "available_scenarios": len(SCENARIOS)
    }


@app.get("/api/scenarios")
async def list_scenarios():
    """List all available realistic money laundering scenarios."""
    return ScenarioLoader.get_all_scenarios_metadata()


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario_details(scenario_id: str):
    """Retrieve full details and transactions for a specific scenario."""
    try:
        return ScenarioLoader.get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/investigate", response_model=InvestigationResult)
async def run_investigation(req: InvestigationRequest):
    """
    Run complete multi-agent investigation synchronously.
    """
    transactions: List[Transaction] = []
    scenario_name = "Custom Ingestion Stream"

    if req.scenario_id:
        try:
            sc = ScenarioLoader.get_scenario(req.scenario_id)
            transactions = ScenarioLoader.load_scenario_transactions(req.scenario_id)
            scenario_name = sc["name"]
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    elif req.transactions:
        transactions = req.transactions
    else:
        raise HTTPException(status_code=400, detail="Must provide either scenario_id or transactions list.")

    result = await orchestrator.run_investigation(
        transactions=transactions,
        scenario_name=scenario_name,
        focus_entity=req.focus_entity
    )

    # Store SAR and investigation for retrieval
    sar_repository[result.sar_draft.sar_id] = result.sar_draft
    investigation_repository[result.investigation_id] = result

    return result


@app.get("/api/investigate/stream")
async def stream_investigation(
    scenario_id: Optional[str] = Query(None),
    focus_entity: Optional[str] = Query(None)
):
    """
    Server-Sent Events (SSE) endpoint to stream agent reasoning steps in real-time.
    """
    transactions: List[Transaction] = []
    scenario_name = "Live Agent Stream"

    if scenario_id:
        try:
            sc = ScenarioLoader.get_scenario(scenario_id)
            transactions = ScenarioLoader.load_scenario_transactions(scenario_id)
            scenario_name = sc["name"]
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        # Default to first scenario
        sc = ScenarioLoader.get_scenario("structuring_ring")
        transactions = ScenarioLoader.load_scenario_transactions("structuring_ring")
        scenario_name = sc["name"]

    async def event_generator():
        try:
            async for event_packet in orchestrator.stream_investigation(
                transactions=transactions,
                scenario_name=scenario_name,
                focus_entity=focus_entity
            ):
                if event_packet.get("event") == "complete":
                    data = event_packet["data"]
                    sar_data = data.get("sar_draft")
                    if sar_data and "sar_id" in sar_data:
                        sar_repository[sar_data["sar_id"]] = SARDraft(**sar_data)
                
                event_type = event_packet["event"]
                event_json = json.dumps(event_packet["data"])
                yield f"event: {event_type}\ndata: {event_json}\n\n"
        except Exception as e:
            err_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {err_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


class SARSignOffRequest(BaseModel):
    sar_id: str
    reviewer_name: str
    reviewer_notes: Optional[str] = ""
    decision: str = "APPROVED"  # APPROVED, REJECTED, ESCALATED


@app.post("/api/sar/signoff")
async def sign_off_sar(req: SARSignOffRequest):
    """
    Human-in-the-loop compliance officer sign-off on generated SAR draft.
    """
    sar = sar_repository.get(req.sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail=f"SAR '{req.sar_id}' not found in active repository.")

    sar.status = f"{req.decision} by {req.reviewer_name}"
    sar_repository[req.sar_id] = sar

    return {
        "status": "SUCCESS",
        "sar_id": sar.sar_id,
        "filing_status": sar.status,
        "notes": req.reviewer_notes
    }


@app.get("/api/sar/{sar_id}")
async def get_sar_report(sar_id: str):
    """Retrieve full SAR draft record."""
    sar = sar_repository.get(sar_id)
    if not sar:
        raise HTTPException(status_code=404, detail=f"SAR '{sar_id}' not found.")
    return sar


# Mount Static Files for Modern Dashboard Frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FinAudit AI Backend is Running. Frontend not yet compiled."}
