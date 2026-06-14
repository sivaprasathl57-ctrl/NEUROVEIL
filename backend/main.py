"""
AI Cyber Investigation System — Backend API
Version 3.0 — Real-World Production Ready
Features: SQLite persistence, OSINT enrichment, evidence management,
          suspect watchlist, BNS 2023 legal framework, bank freeze letters
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json, asyncio, uuid, hashlib, os, shutil
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from agents.investigation_orchestrator import InvestigationOrchestrator
from core.websocket_manager import WebSocketManager
from agents.multi_case_correlation_agent import correlate_multiple_cases
from agents.behavioral_profiling_agent import profile_suspect_behavior
from agents.blockchain_intelligence_agent import trace_crypto_transactions
from agents.predictive_risk_engine import predict_escalation_risk, detect_anomalies, forecast_victim_vulnerability, forecast_financial_impact
from agents.ioc_export_engine import generate_advanced_iocs, generate_threat_report
from agents.osint_enrichment_agent import run_full_osint
from agents.legal_report_agent import generate_bank_freeze_letter
from services.pdf_generator import generate_fir_pdf, generate_report_pdf, generate_dossier_pdf
from services.database import (
    init_db, save_case, load_case, load_all_cases, load_case_stats,
    save_approval, load_pending_approvals, load_all_approvals,
    add_evidence, get_evidence_list, get_custody_log,
    add_to_watchlist, check_watchlist, get_watchlist_all,
    log_audit
)

# ── Init DB ──────────────────────────────────────────────────────────────────
init_db()

# ── Evidence storage directory ────────────────────────────────────────────────
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence_files")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

app = FastAPI(
    title="AI Cyber Investigation System",
    version="3.0",
    description="Real-world AI-powered cybercrime investigation for Indian law enforcement"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_manager = WebSocketManager()
orchestrator = InvestigationOrchestrator(ws_manager)

# In-memory cache (backed by SQLite)
investigations: dict = {}
pending_approvals: dict = {}

# ── Load existing cases from DB into memory on startup ────────────────────────
def _load_all_from_db():
    for case in load_all_cases():
        investigations[case["case_id"]] = case
    for appr in load_all_approvals():
        pending_approvals[appr["approval_id"]] = appr

_load_all_from_db()


# ── Helper: persist case to DB ────────────────────────────────────────────────
def _persist_case(case_id: str):
    if case_id in investigations:
        save_case(case_id, investigations[case_id])


def _persist_approval(approval_id: str):
    if approval_id in pending_approvals:
        save_approval(approval_id, pending_approvals[approval_id])


# ─────────────────────────────────────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "AI Cyber Investigation System Online",
        "version": "3.0",
        "features": [
            "Real Groq LLaMA 3.3 70B AI",
            "SQLite Persistent Storage",
            "OSINT Enrichment (IP/WHOIS/URLhaus)",
            "Evidence Chain of Custody",
            "Suspect Watchlist",
            "BNS 2023 Legal Framework",
            "Bank Freeze Letter Generation",
            "Multi-file Evidence Upload"
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# COMPLAINT SUBMISSION
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/complaint/submit")
async def submit_complaint(
    complaint_text: str = Form(...),
    victim_name: str = Form(...),
    victim_contact: str = Form(...),
    transaction_ids: str = Form(""),
    upi_ids: str = Form(""),
    urls: str = Form(""),
    amount_lost: str = Form("0"),
    # New real-world fields
    incident_date: str = Form(""),
    incident_time: str = Form(""),
    platform: str = Form(""),        # WhatsApp, Telegram, Phone, Email, Website, UPI App
    device_type: str = Form(""),     # Mobile, Laptop, Desktop
    suspect_phones: str = Form(""),
    suspect_emails: str = Form(""),
    victim_bank: str = Form(""),
    victim_account_last4: str = Form(""),
    police_ack_number: str = Form(""),  # If already filed offline
    file: Optional[UploadFile] = File(None)
):
    case_id = f"CYB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    complaint_data = {
        "case_id": case_id,
        "complaint_text": complaint_text,
        "victim_name": victim_name,
        "victim_contact": victim_contact,
        "transaction_ids": transaction_ids,
        "upi_ids": upi_ids,
        "urls": urls,
        "amount_lost": amount_lost,
        "incident_date": incident_date,
        "incident_time": incident_time,
        "platform": platform,
        "device_type": device_type,
        "suspect_phones": suspect_phones,
        "suspect_emails": suspect_emails,
        "victim_bank": victim_bank,
        "victim_account_last4": victim_account_last4,
        "police_ack_number": police_ack_number,
        "status": "investigating",
        "submitted_at": datetime.now().isoformat(),
        "file_name": file.filename if file else None
    }

    investigations[case_id] = complaint_data

    # Handle initial file upload
    if file and file.filename:
        try:
            case_dir = os.path.join(EVIDENCE_DIR, case_id)
            os.makedirs(case_dir, exist_ok=True)
            file_path = os.path.join(case_dir, file.filename)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            file_hash = hashlib.sha256(content).hexdigest()
            add_evidence(case_id, file.filename, file_path,
                        file.content_type, len(content), file_hash, "complainant")
        except Exception as e:
            print(f"File upload error: {e}")

    # Persist to DB
    save_case(case_id, complaint_data)
    log_audit(case_id, "CASE_CREATED", "system", f"Complaint submitted by {victim_name}")

    # Initiate step-by-step case workflow
    asyncio.create_task(
        orchestrator.initiate_case(case_id, complaint_data, investigations, pending_approvals)
    )

    return {"case_id": case_id, "message": "Case registered. Awaiting initial authorization.", "status": "pending_authorization"}


# ─────────────────────────────────────────────────────────────────────────────
# CASE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/investigation/{case_id}")
async def get_investigation(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/api/investigations")
async def list_investigations():
    return load_all_cases()


@app.get("/api/statistics")
async def get_statistics():
    """Real-time dashboard statistics from DB."""
    return load_case_stats()


# ─────────────────────────────────────────────────────────────────────────────
# APPROVALS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/approvals/pending")
async def get_pending_approvals():
    return load_pending_approvals()


@app.get("/api/approvals/all")
async def get_all_approvals():
    return load_all_approvals()


@app.post("/api/approval/{approval_id}")
async def process_approval(
    approval_id: str,
    decision: str = Form(...),
    officer_notes: str = Form(""),
    officer_id: str = Form("OFFICER")
):
    approval = pending_approvals.get(approval_id)
    if not approval:
        approval_data = load_all_approvals()
        approval = next((a for a in approval_data if a["approval_id"] == approval_id), None)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval["decision"] = decision
    approval["officer_notes"] = officer_notes
    approval["officer_id"] = officer_id
    approval["decided_at"] = datetime.now().isoformat()
    approval["status"] = "decided"

    pending_approvals[approval_id] = approval
    save_approval(approval_id, approval)

    case_id = approval["case_id"]
    log_audit(case_id, f"APPROVAL_{decision.upper()}", officer_id,
              f"{approval.get('action')} — {officer_notes or 'No notes'}")

    asyncio.create_task(
        orchestrator.process_approval_decision(
            case_id, approval_id, decision, officer_notes, investigations, pending_approvals
        )
    )

    return {"message": f"Approval {decision}", "approval_id": approval_id}


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────
@app.websocket("/ws/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: str):
    await ws_manager.connect(websocket, case_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, case_id)


@app.websocket("/ws/dashboard/live")
async def dashboard_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket, "dashboard")
    try:
        while True:
            await asyncio.sleep(5)
            stats = load_case_stats()
            await ws_manager.send_personal_message(
                json.dumps({"type": "stats", "data": stats}),
                websocket
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "dashboard")


# ─────────────────────────────────────────────────────────────────────────────
# OSINT ENRICHMENT
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/osint/{case_id}")
async def get_osint_enrichment(case_id: str):
    """Run real OSINT enrichment on extracted entities (IP geo, WHOIS, URL threats)."""
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    entities = case.get("complaint_analysis", {}).get("extracted_entities", {})

    # Also add complaint-level URLs/phones if not yet analyzed
    if case.get("urls") and not entities.get("urls"):
        entities["urls"] = [u.strip() for u in case.get("urls", "").split(",") if u.strip()]
    if case.get("suspect_phones") and not entities.get("phone_numbers"):
        entities["phone_numbers"] = [p.strip() for p in case.get("suspect_phones", "").split(",") if p.strip()]

    osint_result = await run_full_osint(case_id, entities)

    if "advanced_analysis" not in investigations.get(case_id, {}):
        if case_id in investigations:
            investigations[case_id]["advanced_analysis"] = {}
    if case_id in investigations:
        investigations[case_id]["advanced_analysis"]["osint"] = osint_result
        _persist_case(case_id)

    # Add suspicious IPs/domains to watchlist
    for ip_info in osint_result.get("ip_analysis", []):
        if ip_info.get("is_vpn_likely") or ip_info.get("country_code") not in ["IN", "Local", ""]:
            add_to_watchlist(
                ip_info.get("ip", ""), "ip", case_id, "high",
                f"Foreign/VPN IP from {ip_info.get('country', 'Unknown')}"
            )

    log_audit(case_id, "OSINT_ENRICHMENT", "AI_System",
              f"OSINT completed. {len(osint_result.get('key_findings', []))} findings.")

    return osint_result


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/evidence/upload/{case_id}")
async def upload_evidence(
    case_id: str,
    notes: str = Form(""),
    uploaded_by: str = Form("officer"),
    files: list[UploadFile] = File(...)
):
    """Upload one or more evidence files with automatic SHA-256 hashing."""
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    uploaded = []
    case_dir = os.path.join(EVIDENCE_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    for f in files:
        try:
            content = await f.read()
            file_hash = hashlib.sha256(content).hexdigest()

            # Save with hash-prefixed name to avoid collisions
            safe_name = f"{file_hash[:8]}_{f.filename}"
            file_path = os.path.join(case_dir, safe_name)
            with open(file_path, "wb") as fp:
                fp.write(content)

            ev_id = add_evidence(
                case_id, f.filename, file_path,
                f.content_type, len(content), file_hash,
                uploaded_by, notes
            )
            uploaded.append({
                "evidence_id": ev_id,
                "file_name": f.filename,
                "file_size": len(content),
                "sha256": file_hash,
                "uploaded_by": uploaded_by
            })
        except Exception as e:
            uploaded.append({"file_name": f.filename, "error": str(e)})

    log_audit(case_id, "EVIDENCE_UPLOADED", uploaded_by,
              f"{len(uploaded)} file(s) uploaded")

    return {"case_id": case_id, "uploaded": uploaded}


@app.get("/api/evidence/{case_id}")
async def get_evidence(case_id: str):
    """Get all evidence files and chain-of-custody log for a case."""
    return {
        "case_id": case_id,
        "evidence": get_evidence_list(case_id),
        "custody_log": get_custody_log(case_id)
    }


@app.get("/api/evidence/{case_id}/download/{evidence_id}")
async def download_evidence(case_id: str, evidence_id: int):
    """Download a specific evidence file."""
    evidence_list = get_evidence_list(case_id)
    ev = next((e for e in evidence_list if e["id"] == evidence_id), None)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    file_path = ev["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type=ev.get("file_type", "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={ev['file_name']}"}
    )


# ─────────────────────────────────────────────────────────────────────────────
# WATCHLIST / CROSS-CASE MATCHING
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/watchlist/check")
async def check_watchlist_endpoint(request_data: dict):
    """Check a list of indicators against the suspect watchlist."""
    indicators = request_data.get("indicators", [])
    matches = check_watchlist(indicators)
    return {"matches": matches, "total_matches": len(matches)}


@app.get("/api/watchlist")
async def get_watchlist():
    """Get all suspects/indicators in the watchlist."""
    return {"watchlist": get_watchlist_all()}


@app.post("/api/watchlist/add")
async def add_watchlist_entry(request_data: dict):
    """Manually add an indicator to the watchlist."""
    add_to_watchlist(
        request_data.get("indicator"),
        request_data.get("type", "other"),
        request_data.get("case_id", "manual"),
        request_data.get("risk_level", "medium"),
        request_data.get("notes", "")
    )
    return {"status": "added"}


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED ANALYSIS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/correlate-cases")
async def correlate_cases(request_data: dict):
    case_ids = request_data.get("case_ids", [])
    cases_data = {}
    for cid in case_ids:
        c = investigations.get(cid) or load_case(cid)
        if c:
            cases_data[cid] = c

    if len(cases_data) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 valid cases to correlate")

    result = await correlate_multiple_cases(case_ids, cases_data)
    return result


@app.get("/api/behavioral-profile/{case_id}")
async def get_behavioral_profile(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    result = await profile_suspect_behavior(case_id, case, case)

    if case_id in investigations:
        if "advanced_analysis" not in investigations[case_id]:
            investigations[case_id]["advanced_analysis"] = {}
        investigations[case_id]["advanced_analysis"]["behavioral_profile"] = result
        _persist_case(case_id)

    return result


@app.get("/api/blockchain-forensics/{case_id}")
async def get_blockchain_forensics(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    wallet_addresses = case.get("complaint_analysis", {}).get("extracted_entities", {}).get("crypto_wallets", [])
    result = await trace_crypto_transactions(case_id, wallet_addresses, case)

    if case_id in investigations:
        if "advanced_analysis" not in investigations[case_id]:
            investigations[case_id]["advanced_analysis"] = {}
        investigations[case_id]["advanced_analysis"]["blockchain_forensics"] = result
        _persist_case(case_id)

    return result


@app.get("/api/predictive-risk/{case_id}")
async def get_predictive_risk(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    suspect_profile = case.get("fraud_classification", {}).get("suspect_profile", {})
    all_cases = load_all_cases()

    amounts = []
    for c in all_cases:
        try:
            amounts.append(float(c.get("amount_lost", 0)))
        except (ValueError, TypeError):
            pass
    avg_amount = sum(amounts) / len(amounts) if amounts else 0.0

    historical_patterns = {
        "avg_amount": f"{avg_amount:.2f}",
        "typical_victim": "Individual",
        "typical_timeframe": "Immediate",
        "total_cases": len(all_cases)
    }

    victim_profile = {
        "name": case.get("victim_name"),
        "contact": case.get("victim_contact"),
        "complaint_text": case.get("complaint_text")
    }

    escalation = await predict_escalation_risk(case_id, case, suspect_profile)
    anomalies = await detect_anomalies(case_id, case, historical_patterns)
    vulnerability = await forecast_victim_vulnerability(victim_profile)
    financial = await forecast_financial_impact(case, {c["case_id"]: c for c in all_cases})

    result = {
        "escalation_risk": escalation,
        "anomalies": anomalies,
        "victim_vulnerability": vulnerability,
        "financial_forecast": financial
    }

    if case_id in investigations:
        if "advanced_analysis" not in investigations[case_id]:
            investigations[case_id]["advanced_analysis"] = {}
        investigations[case_id]["advanced_analysis"]["predictive_risk"] = result
        _persist_case(case_id)

    return result


@app.get("/api/ioc-export/{case_id}")
async def get_ioc_export(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    iocs = await generate_advanced_iocs(case_id, case)

    if case_id in investigations:
        if "advanced_analysis" not in investigations[case_id]:
            investigations[case_id]["advanced_analysis"] = {}
        investigations[case_id]["advanced_analysis"]["iocs"] = iocs
        _persist_case(case_id)

    return iocs


@app.get("/api/threat-report/{case_id}")
async def get_threat_report(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    report = await generate_threat_report(case_id, case)

    if case_id in investigations:
        if "advanced_analysis" not in investigations[case_id]:
            investigations[case_id]["advanced_analysis"] = {}
        investigations[case_id]["advanced_analysis"]["threat_report"] = report
        _persist_case(case_id)

    return report


@app.get("/api/investigation/{case_id}/full-advanced")
async def get_full_advanced_analysis(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = case.copy()
    if "advanced_analysis" not in result:
        result["advanced_analysis"] = {"note": "Run individual endpoints to generate advanced analysis"}
    return result


# ─────────────────────────────────────────────────────────────────────────────
# MONEY RECOVERY / COURT REFUND
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/investigation/{case_id}/initiate-recovery")
async def initiate_recovery(
    case_id: str,
    account_or_upi: str = Form(...),
    amount: str = Form(...)
):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Call AI agent to generate petition and NOC text
    from agents.legal_report_agent import generate_court_refund_petition
    petition_draft = await generate_court_refund_petition(case_id, case, account_or_upi, amount)
    
    # Store drafts in the case
    case["recovery_status"] = "initiated"
    try:
        amount_val = float(amount.replace(",", "").strip())
    except:
        amount_val = 0.0
    case["recovered_amount"] = amount_val
    case["refund_petition_draft"] = petition_draft
    investigations[case_id] = case
    _persist_case(case_id)
    
    # Create the pending approval request for 'refund_authorization'
    approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
    approval_data = {
        "approval_id": approval_id,
        "case_id": case_id,
        "action": "Authorize Judicial Money Recovery & Refund",
        "details": [
            f"Victim: {case.get('victim_name')}",
            f"Target Account/UPI: {account_or_upi}",
            f"Recovery Amount: Rs. {amount}"
        ],
        "reason": f"Initiating recovery of frozen funds under Sec 503 BNSS 2023. Release requested from suspect account/UPI: {account_or_upi} back to victim bank account. Requires sign-off of Judicial Release Petition and NOC.",
        "ai_confidence": 99,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "type": "refund_authorization",
        "meta": {
            "amount": amount,
            "account_or_upi": account_or_upi
        }
    }
    
    pending_approvals[approval_id] = approval_data
    save_approval(approval_id, approval_data)
    
    # Send WebSocket update and approval request
    await orchestrator.send_approval_request(
        case_id, approval_id,
        "Authorize Judicial Refund",
        f"Refund request of Rs. {amount} initiated. Awaiting authorization.",
        approval_data
    )
    
    # Add audit log
    log_audit(case_id, "RECOVERY_INITIATED", "officer", f"Recovery of Rs. {amount} from {account_or_upi} initiated.")
    
    await orchestrator.send_update(
        case_id, "recovery_initiated",
        f"⏳ Money recovery initiated for Rs. {amount} from {account_or_upi}. Awaiting judicial authorization.",
        data={"recovery_status": "initiated", "recovered_amount": amount_val},
        progress=90
    )
    
    return {"status": "initiated", "approval_id": approval_id}


# ─────────────────────────────────────────────────────────────────────────────
# BANK FREEZE LETTER
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/investigation/{case_id}/bank-freeze-letter")
async def get_bank_freeze_letter(case_id: str):
    """Generate official bank account freeze request letter."""
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    freeze_recs = case.get("banking_investigation", {}).get("freeze_recommendations", [])
    if not freeze_recs:
        return {"error": "No freeze recommendations yet — run investigation first"}

    letter = await generate_bank_freeze_letter(case_id, freeze_recs, case)

    if case_id in investigations:
        investigations[case_id]["bank_freeze_letter"] = letter
        _persist_case(case_id)

    return {"case_id": case_id, "letter": letter}


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/audit/{case_id}")
async def get_audit_log(case_id: str):
    from services.database import get_conn
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE case_id=? ORDER BY timestamp DESC", (case_id,)
        ).fetchall()
        return {"audit_log": [dict(r) for r in rows]}
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# PDF DOWNLOADS
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/investigation/{case_id}/download/fir")
async def download_fir(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        return Response(content="Case not found", status_code=404)
    log_audit(case_id, "PDF_DOWNLOAD_FIR", "officer", "FIR PDF downloaded")
    pdf_bytes = generate_fir_pdf(case_id, case)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=FIR_{case_id}.pdf"}
    )


@app.get("/api/investigation/{case_id}/download/report")
async def download_report(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        return Response(content="Case not found", status_code=404)
    case_copy = case.copy()
    case_copy["evidence"] = get_evidence_list(case_id)
    case_copy["custody_log"] = get_custody_log(case_id)
    log_audit(case_id, "PDF_DOWNLOAD_REPORT", "officer", "Investigation Report PDF downloaded")
    pdf_bytes = generate_report_pdf(case_id, case_copy)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Case_Report_{case_id}.pdf"}
    )


@app.get("/api/investigation/{case_id}/download/dossier")
async def download_dossier(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        return Response(content="Case not found", status_code=404)
    case_copy = case.copy()
    case_copy["evidence"] = get_evidence_list(case_id)
    case_copy["custody_log"] = get_custody_log(case_id)
    log_audit(case_id, "PDF_DOWNLOAD_DOSSIER", "officer", "Full Case Dossier PDF downloaded")
    pdf_bytes = generate_dossier_pdf(case_id, case_copy)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Case_Dossier_{case_id}.pdf"}
    )


@app.get("/api/investigation/{case_id}/download/refund-petition")
async def download_refund_petition(case_id: str):
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        return Response(content="Case not found", status_code=404)
    log_audit(case_id, "PDF_DOWNLOAD_REFUND_PETITION", "officer", "Refund Petition PDF downloaded")
    from services.pdf_generator import generate_refund_petition_pdf
    pdf_bytes = generate_refund_petition_pdf(case_id, case)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Refund_Petition_{case_id}.pdf"}
    )


# ─────────────────────────────────────────────────────────────────────────────
# INVESTIGATION TIMELINE
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/investigation/{case_id}/timeline")
async def get_timeline(case_id: str):
    """Get structured investigation timeline combining crime events and investigation stages."""
    case = investigations.get(case_id) or load_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Crime event timeline from AI analysis
    crime_timeline = case.get("complaint_analysis", {}).get("timeline_of_events", [])

    # Investigation stage timeline from logs
    inv_log = case.get("investigation_log", [])

    # Banking transaction chain
    tx_chain = case.get("banking_investigation", {}).get("transaction_analysis", {}).get("transaction_chain", [])
    tx_timeline = [
        {"time": tx.get("timestamp", ""), "event": f"Money transfer: {tx['from']} → {tx['to']} ₹{tx['amount']}", "actor": "suspect", "type": "financial"}
        for tx in tx_chain
    ]

    return {
        "case_id": case_id,
        "crime_timeline": crime_timeline,
        "investigation_stages": [
            {"time": log.get("time", ""), "event": log.get("message", ""), "type": "investigation"}
            for log in inv_log
        ],
        "transaction_timeline": tx_timeline,
        "risk_timeline": case.get("risk_assessment", {}).get("timeline_reconstruction", [])
    }
