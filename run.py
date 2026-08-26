"""
FinAudit AI Application Launcher
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("[*] Launching FinAudit AI - Autonomous AML Forensic Intelligence Swarm")
    print("[*] Dashboard UI: http://localhost:8000")
    print("[*] API Documentation: http://localhost:8000/docs")
    print("=" * 70)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
