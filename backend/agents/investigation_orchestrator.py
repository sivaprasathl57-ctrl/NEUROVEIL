import json
import asyncio
import uuid
from datetime import datetime

from agents.complaint_analysis_agent import analyze_complaint
from agents.fraud_classification_agent import classify_fraud
from agents.banking_investigation_agent import investigate_banking
from agents.graph_intelligence_agent import build_fraud_graph
from agents.risk_prediction_agent import predict_risk
from agents.legal_report_agent import generate_fir_draft, generate_investigation_report
from agents.osint_enrichment_agent import run_full_osint
from core.websocket_manager import WebSocketManager
from services.database import save_case, save_approval, add_to_watchlist, log_audit


class InvestigationOrchestrator:
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    async def send_update(self, case_id: str, stage: str, message: str, data: dict = None, progress: int = 0):
        payload = {
            "type": "investigation_update",
            "case_id": case_id,
            "stage": stage,
            "message": message,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        await self.ws_manager.send_to_room(json.dumps(payload), case_id)
        await self.ws_manager.send_to_room(json.dumps(payload), "dashboard")

    async def send_approval_request(self, case_id: str, approval_id: str, action: str, reason: str, data: dict):
        payload = {
            "type": "approval_request",
            "case_id": case_id,
            "approval_id": approval_id,
            "action": action,
            "reason": reason,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.ws_manager.send_to_room(json.dumps(payload), case_id)
        await self.ws_manager.send_to_room(json.dumps(payload), "dashboard")

    def _persist(self, case_id: str, investigations: dict):
        """Persist case to SQLite after each stage update."""
        if case_id in investigations:
            save_case(case_id, investigations[case_id])

    def _add_entities_to_watchlist(self, case_id: str, entities: dict, risk_level: str = "medium"):
        """Auto-populate suspect watchlist from extracted entities."""
        for upi in entities.get("upi_ids", []):
            if upi:
                add_to_watchlist(upi, "upi_id", case_id, risk_level, "Extracted from complaint")
        for phone in entities.get("phone_numbers", []):
            if phone:
                add_to_watchlist(phone, "phone", case_id, risk_level, "Extracted from complaint")
        for phone in entities.get("whatsapp_numbers", []):
            if phone:
                add_to_watchlist(phone, "whatsapp", case_id, risk_level, "WhatsApp number from complaint")
        for email in entities.get("email_addresses", []):
            if email:
                add_to_watchlist(email, "email", case_id, risk_level, "Extracted from complaint")
        for url in entities.get("urls", []):
            if url:
                add_to_watchlist(url, "url", case_id, "high", "Phishing/scam URL from complaint")
        for wallet in entities.get("crypto_wallets", []):
            if wallet:
                add_to_watchlist(wallet, "crypto_wallet", case_id, "high", "Cryptocurrency wallet from complaint")
        for acct in entities.get("bank_accounts", []):
            if acct:
                add_to_watchlist(acct, "bank_account", case_id, risk_level, "Bank account from complaint")
        for name in entities.get("suspect_names", []):
            if name and name.lower() not in ["unknown", "scammer", "na", "n/a"]:
                add_to_watchlist(name, "suspect_name", case_id, risk_level, "Named suspect")

    async def initiate_case(self, case_id: str, complaint_data: dict, investigations: dict, pending_approvals: dict):
        try:
            investigations[case_id] = complaint_data
            investigations[case_id]["investigation_log"] = []
            investigations[case_id]["progress"] = 0
            investigations[case_id]["status"] = "pending_authorization"
            
            def log(msg):
                investigations[case_id]["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log("Complaint received. Case registered as pending authorization.")
            log_audit(case_id, "CASE_CREATED", "system", f"Complaint submitted by {complaint_data.get('victim_name')}")

            # Create approval request for Gate 1: Case Authorization
            approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
            approval_data = {
                "approval_id": approval_id,
                "case_id": case_id,
                "action": "Authorize Cybercrime Investigation",
                "details": [
                    f"Complainant: {complaint_data.get('victim_name')}",
                    f"Reported Loss: ₹{complaint_data.get('amount_lost')}",
                    f"Platform: {complaint_data.get('platform') or 'Not Specified'}"
                ],
                "reason": f"New complaint registered from {complaint_data.get('victim_name')}. Total loss reported: ₹{complaint_data.get('amount_lost')}. Requires authorization to trigger AI multi-agent pipeline.",
                "ai_confidence": 100,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "type": "case_authorization"
            }
            pending_approvals[approval_id] = approval_data
            save_approval(approval_id, approval_data)

            self._persist(case_id, investigations)

            # Send WS alerts
            await self.send_approval_request(
                case_id, approval_id,
                "Authorize Investigation",
                f"New complaint from {complaint_data.get('victim_name')} requires initial authorization to investigate.",
                approval_data
            )
            await self.send_update(case_id, "pending_authorization", "📋 Case registered. Awaiting initial authorization from supervisor to proceed.", progress=0)

        except Exception as e:
            error_msg = f"Error registering case: {str(e)}"
            investigations[case_id] = complaint_data
            investigations[case_id]["status"] = "error"
            investigations[case_id]["error"] = error_msg
            self._persist(case_id, investigations)
            log_audit(case_id, "CASE_REGISTRATION_ERROR", "system", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def run_stage_complaint_analysis(self, case_id: str, investigations: dict, pending_approvals: dict):
        try:
            case_data = investigations.get(case_id)
            if not case_data:
                return

            def log(msg):
                case_data["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log_audit(case_id, "INVESTIGATION_STARTED", "AI_System", "Multi-agent investigation pipeline initiated after authorization")
            log("Initial Case Authorization approved. Starting Stage 1: Complaint Analysis.")
            
            case_data["status"] = "running_complaint_analysis"
            case_data["progress"] = 5
            self._persist(case_id, investigations)
            await self.send_update(case_id, "complaint_analysis", "🔍 Analyzing complaint and extracting digital entities...", progress=5)

            complaint_analysis = await analyze_complaint(case_data)
            case_data["complaint_analysis"] = complaint_analysis
            case_data["progress"] = 12
            log(f"Extracted {len(complaint_analysis.get('extracted_entities', {}))} entity categories. Scam type: {complaint_analysis.get('scam_type')}")

            # Auto-populate watchlist from extracted entities
            entities = complaint_analysis.get("extracted_entities", {})
            self._add_entities_to_watchlist(case_id, entities, "medium")
            log(f"Watchlist updated with extracted suspect indicators")

            # Create approval request for Gate 2: OSINT Clearance
            approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
            
            details_list = []
            for k, v in entities.items():
                if v:
                    details_list.append(f"{k.replace('_', ' ').title()}: {', '.join(v)}")
            
            approval_data = {
                "approval_id": approval_id,
                "case_id": case_id,
                "action": "Authorize OSINT & External Enrichment",
                "details": details_list,
                "reason": f"Complaint analysis completed. Extracted indicators require active lookup (IP Geolocation via ipapi.co, domain WHOIS via RDAP, URL threat status via URLhaus). Confirm clearance to scan external endpoints.",
                "ai_confidence": 95,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "type": "osint_approval"
            }
            pending_approvals[approval_id] = approval_data
            save_approval(approval_id, approval_data)

            case_data["status"] = "awaiting_osint_approval"
            self._persist(case_id, investigations)

            # Send updates
            await self.send_approval_request(
                case_id, approval_id,
                "Authorize OSINT Clearance",
                "Entities extracted. Requesting approval to run active OSINT lookup on IPs, domains, and phone numbers.",
                approval_data
            )
            await self.send_update(case_id, "awaiting_osint_approval",
                f"✅ Entities extracted. Awaiting OSINT lookup authorization. Scam type: {complaint_analysis.get('scam_type', 'Unknown')}.",
                data=complaint_analysis, progress=12)

        except Exception as e:
            error_msg = f"Complaint analysis stage error: {str(e)}"
            case_data = investigations.get(case_id)
            if case_data:
                case_data["status"] = "error"
                case_data["error"] = error_msg
                self._persist(case_id, investigations)
            log_audit(case_id, "STAGE_ERROR_COMPLAINT_ANALYSIS", "AI_System", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def run_stage_analysis_and_banking(self, case_id: str, investigations: dict, pending_approvals: dict):
        try:
            case_data = investigations.get(case_id)
            if not case_data:
                return

            def log(msg):
                case_data["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log("OSINT Clearance approved. Starting Stage 2: OSINT Enrichment, Fraud Classification, and Banking Investigation.")
            case_data["status"] = "running_analysis"
            case_data["progress"] = 18
            self._persist(case_id, investigations)

            # OSINT Lookups
            await self.send_update(case_id, "osint_enrichment", "🌐 Running OSINT lookups (IP geo, WHOIS, phone carrier, URL threat check)...", progress=18)
            entities = case_data.get("complaint_analysis", {}).get("extracted_entities", {})
            try:
                osint_data = await run_full_osint(case_id, entities)
                case_data["osint_enrichment"] = osint_data
                findings_count = len(osint_data.get("key_findings", []))
                threat_level = osint_data.get("summary", {}).get("threat_level", "unknown")
                log(f"OSINT complete: {findings_count} findings. Threat level: {threat_level}")
                await self.send_update(case_id, "osint_done",
                    f"✅ OSINT enrichment done. {findings_count} findings.",
                    data=osint_data, progress=25)
            except Exception as e:
                log(f"OSINT enrichment skipped: {str(e)}")
                await self.send_update(case_id, "osint_done",
                    "⚠️ OSINT enrichment completed with limited results", progress=25)

            case_data["progress"] = 28
            self._persist(case_id, investigations)

            # Fraud Classification
            await self.send_update(case_id, "fraud_classification", "🧠 Classifying fraud patterns and analyzing modus operandi...", progress=28)
            fraud_classification = await classify_fraud(
                case_id,
                entities,
                case_data.get("complaint_text", ""),
                case_data.get("amount_lost", "0")
            )
            case_data["fraud_classification"] = fraud_classification
            case_data["progress"] = 38
            log(f"Fraud probability: {fraud_classification.get('fraud_probability')}%. Modus Operandi classified.")

            # Update watchlist risk levels based on fraud probability
            fraud_prob = fraud_classification.get("fraud_probability", 0)
            if fraud_prob >= 80:
                self._add_entities_to_watchlist(case_id, entities, "critical")
            elif fraud_prob >= 60:
                self._add_entities_to_watchlist(case_id, entities, "high")

            self._persist(case_id, investigations)
            await self.send_update(case_id, "fraud_classification_done",
                f"✅ Fraud classified. Probability: {fraud_classification.get('fraud_probability')}%",
                data=fraud_classification, progress=38)

            # Banking Investigation
            await self.send_update(case_id, "banking_investigation", "🏦 Tracing transaction chains and identifying mule accounts...", progress=44)
            banking_investigation = await investigate_banking(
                case_id,
                entities,
                fraud_classification,
                case_data.get("complaint_text", "")
            )
            case_data["banking_investigation"] = banking_investigation
            case_data["progress"] = 52
            freeze_count = len(banking_investigation.get("freeze_recommendations", []))
            log(f"Transaction chain mapped. {freeze_count} freeze recommendations generated.")

            # Add freeze targets to watchlist
            for freeze_rec in banking_investigation.get("freeze_recommendations", []):
                acct = freeze_rec.get("account_or_upi", "")
                if acct:
                    add_to_watchlist(acct, "freeze_target", case_id, "critical",
                                   f"Freeze recommended: {freeze_rec.get('reason', '')}")

            self._persist(case_id, investigations)
            await self.send_update(case_id, "banking_done",
                f"✅ Banking analysis complete. {freeze_count} suspect accounts flagged.",
                data=banking_investigation, progress=52)

            # Create approval request for Gate 3: Bank Account Freeze (if applicable)
            if freeze_count > 0:
                approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
                
                details_list = []
                for fr in banking_investigation.get("freeze_recommendations", []):
                    details_list.append(f"{fr.get('account_or_upi')} ({fr.get('bank_name', 'Unknown Bank')}) — {fr.get('priority', '').upper()} Priority")

                approval_data = {
                    "approval_id": approval_id,
                    "case_id": case_id,
                    "action": "Bank Account Freeze Request",
                    "details": details_list,
                    "reason": f"AI mapping traced funds layering into {freeze_count} suspect accounts. Total suspected amount: ₹{case_data.get('amount_lost')}. Requires authorization to proceed with freeze directives (under Sec 106 BNSS).",
                    "ai_confidence": fraud_classification.get("fraud_probability", 0),
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "type": "bank_freeze"
                }
                pending_approvals[approval_id] = approval_data
                save_approval(approval_id, approval_data)

                case_data["status"] = "awaiting_freeze_approval"
                self._persist(case_id, investigations)

                await self.send_approval_request(
                    case_id, approval_id,
                    "Bank Account Freeze",
                    f"AI recommends freezing {freeze_count} accounts. Human supervisor approval required to proceed.",
                    approval_data
                )
                log(f"⚠️ HUMAN APPROVAL REQUIRED: Bank freeze for {freeze_count} accounts (approval_id: {approval_id})")
                log_audit(case_id, "APPROVAL_REQUESTED", "AI_System",
                         f"Bank freeze approval requested for {freeze_count} accounts")
            else:
                log("No suspect accounts flagged for freezing. Automatically proceeding to Stage 3: Reporting & Network Graph.")
                asyncio.create_task(
                    self.run_stage_reporting(case_id, investigations, pending_approvals)
                )

        except Exception as e:
            error_msg = f"OSINT/Banking stage error: {str(e)}"
            case_data = investigations.get(case_id)
            if case_data:
                case_data["status"] = "error"
                case_data["error"] = error_msg
                self._persist(case_id, investigations)
            log_audit(case_id, "STAGE_ERROR_ANALYSIS_BANKING", "AI_System", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def run_stage_reporting(self, case_id: str, investigations: dict, pending_approvals: dict):
        try:
            case_data = investigations.get(case_id)
            if not case_data:
                return

            def log(msg):
                case_data["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log("Starting Stage 3: Network Graph and Risk Prediction.")
            case_data["status"] = "running_reporting"
            case_data["progress"] = 60
            self._persist(case_id, investigations)

            # Graph Intelligence
            await self.send_update(case_id, "graph_intelligence", "🕸️ Building criminal network graph...", progress=60)
            entities = case_data.get("complaint_analysis", {}).get("extracted_entities", {})
            banking_investigation = case_data.get("banking_investigation", {})
            fraud_classification = case_data.get("fraud_classification", {})

            graph_data = await build_fraud_graph(
                case_id,
                entities,
                banking_investigation,
                fraud_classification
            )
            case_data["graph_intelligence"] = graph_data
            case_data["progress"] = 68
            log(f"Graph built: {graph_data.get('network_summary', {}).get('total_nodes')} nodes mapped.")

            self._persist(case_id, investigations)
            await self.send_update(case_id, "graph_done",
                f"✅ Network graph complete. {graph_data.get('network_summary', {}).get('total_nodes', 0)} nodes mapped.",
                data=graph_data, progress=68)

            # Risk Prediction
            await self.send_update(case_id, "risk_prediction", "⚠️ Calculating risk scores and predicting outcomes...", progress=75)
            
            all_analysis = {
                "complaint_analysis": case_data.get("complaint_analysis", {}),
                "fraud_classification": fraud_classification,
                "banking_investigation": banking_investigation,
                "graph_intelligence": graph_data
            }

            risk_assessment = await predict_risk(case_id, all_analysis)
            case_data["risk_assessment"] = risk_assessment
            case_data["progress"] = 83
            urgency = risk_assessment.get("overall_scores", {}).get("urgency_score", 0)
            log(f"Risk assessment complete. Urgency score: {urgency}/100.")

            self._persist(case_id, investigations)
            await self.send_update(case_id, "risk_done",
                f"✅ Risk assessment complete. Urgency: {urgency}/100.",
                data=risk_assessment, progress=83)

            # Create approval request for Gate 4: Legal Escalation (if urgency >= 75)
            if urgency >= 75:
                approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
                
                details_list = []
                for act in risk_assessment.get("priority_actions", []):
                    details_list.append(f"{act.get('action')} (Deadline: {act.get('deadline')})")

                approval_data = {
                    "approval_id": approval_id,
                    "case_id": case_id,
                    "action": "Legal Escalation to SP/Court",
                    "details": details_list,
                    "reason": f"Urgency score calculated at {urgency}/100 (high risk/narco- nexus / cross-border activity). Requires human clearance to escalate to Cyber SP/Superintendent and initiate prosecution procedures.",
                    "ai_confidence": fraud_classification.get("fraud_probability", 0),
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "type": "legal_escalation"
                }
                pending_approvals[approval_id] = approval_data
                save_approval(approval_id, approval_data)

                case_data["status"] = "awaiting_legal_escalation"
                self._persist(case_id, investigations)

                await self.send_approval_request(
                    case_id, approval_id,
                    "Legal Escalation",
                    f"Urgency score {urgency}/100. High-risk case requires supervisor sign-off to initiate legal escalation.",
                    approval_data
                )
                log(f"⚠️ HUMAN APPROVAL REQUIRED: Legal escalation (approval_id: {approval_id})")
                log_audit(case_id, "ESCALATION_REQUESTED", "AI_System",
                         f"Legal escalation requested (urgency: {urgency}/100)")
            else:
                log("Case urgency score within standard limits. Automatically proceeding to Stage 4: Document Drafting.")
                asyncio.create_task(
                    self.run_stage_generation(case_id, investigations, pending_approvals)
                )

        except Exception as e:
            error_msg = f"Reporting stage error: {str(e)}"
            case_data = investigations.get(case_id)
            if case_data:
                case_data["status"] = "error"
                case_data["error"] = error_msg
                self._persist(case_id, investigations)
            log_audit(case_id, "STAGE_ERROR_REPORTING", "AI_System", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def run_stage_generation(self, case_id: str, investigations: dict, pending_approvals: dict):
        try:
            case_data = investigations.get(case_id)
            if not case_data:
                return

            def log(msg):
                case_data["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log("Starting Stage 4: Legal Reports Generation.")
            case_data["status"] = "generating_reports"
            case_data["progress"] = 88
            self._persist(case_id, investigations)

            # Generate drafts
            await self.send_update(case_id, "legal_reports", "📄 Drafting FIR and investigation report under BNS 2023...", progress=88)
            
            all_analysis = {
                "complaint_analysis": case_data.get("complaint_analysis", {}),
                "fraud_classification": case_data.get("fraud_classification", {}),
                "banking_investigation": case_data.get("banking_investigation", {}),
                "graph_intelligence": case_data.get("graph_intelligence", {}),
                "risk_assessment": case_data.get("risk_assessment", {})
            }

            fir_draft = await generate_fir_draft(case_id, case_data, all_analysis, case_data.get("risk_assessment", {}))
            full_investigation = {**all_analysis, "risk_assessment": case_data.get("risk_assessment", {})}
            investigation_report = await generate_investigation_report(case_id, full_investigation)

            case_data["fir_draft"] = fir_draft
            case_data["investigation_report"] = investigation_report
            case_data["progress"] = 96
            log("FIR draft and narrative investigation report successfully generated.")

            # Also generate bank freeze letters if bank freeze was recommended
            freeze_recs = case_data.get("banking_investigation", {}).get("freeze_recommendations", [])
            if freeze_recs:
                try:
                    log("Drafting bank account freeze request letters based on approved freeze recommendations.")
                    letter = await generate_bank_freeze_letter(case_id, freeze_recs, case_data)
                    case_data["bank_freeze_letter"] = letter
                except Exception as ex:
                    log(f"Bank freeze letter generation skipped: {str(ex)}")

            self._persist(case_id, investigations)
            await self.send_update(case_id, "reports_done", "✅ FIR draft and investigation report generated.", progress=96)

            # Create approval request for Gate 5: Final Sign-off
            approval_id = f"APR-{str(uuid.uuid4())[:8].upper()}"
            approval_data = {
                "approval_id": approval_id,
                "case_id": case_id,
                "action": "FIR & Investigation Report Sign-off",
                "details": [
                    "Review FIR legal draft (BNS / IT Act / PMLA sections)",
                    "Review detailed narrative investigation report",
                    "Verify evidence chain-of-custody inventory",
                    "Digitally sign and authorize filing of reports"
                ],
                "reason": "Draft reports generated successfully. Requires final review, signature, and submission sign-off from the Officer-in-Charge before case closure.",
                "ai_confidence": 98,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "type": "final_signoff"
            }
            pending_approvals[approval_id] = approval_data
            save_approval(approval_id, approval_data)

            case_data["status"] = "awaiting_final_signoff"
            self._persist(case_id, investigations)

            await self.send_approval_request(
                case_id, approval_id,
                "Final Sign-off",
                "Draft reports ready. Human signature/sign-off required to finalize case.",
                approval_data
            )
            log(f"⚠️ HUMAN APPROVAL REQUIRED: Final sign-off (approval_id: {approval_id})")

        except Exception as e:
            error_msg = f"Generation stage error: {str(e)}"
            case_data = investigations.get(case_id)
            if case_data:
                case_data["status"] = "error"
                case_data["error"] = error_msg
                self._persist(case_id, investigations)
            log_audit(case_id, "STAGE_ERROR_GENERATION", "AI_System", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def run_stage_complete(self, case_id: str, investigations: dict):
        try:
            case_data = investigations.get(case_id)
            if not case_data:
                return

            def log(msg):
                case_data["investigation_log"].append({
                    "time": datetime.now().isoformat(),
                    "message": msg
                })

            log("Final Sign-off approved. Closing case file.")
            case_data["status"] = "investigation_complete"
            case_data["completed_at"] = datetime.now().isoformat()
            case_data["progress"] = 100
            
            risk_assessment = case_data.get("risk_assessment", {})
            fraud_classification = case_data.get("fraud_classification", {})

            case_data["final_scores"] = risk_assessment.get("overall_scores", {})
            case_data["alert_type"] = risk_assessment.get("alert_type", "standard")

            log("✅ Full AI investigation complete. Case file signed and locked.")
            log_audit(case_id, "INVESTIGATION_COMPLETE", "officer",
                     f"Case finalized by officer sign-off. Fraud probability: {fraud_classification.get('fraud_probability')}%")

            self._persist(case_id, investigations)

            await self.send_update(case_id, "complete",
                f"🎯 Investigation fully complete! Case files signed, locked and filed under BNS 2023.",
                data={"case_id": case_id, "status": "complete"},
                progress=100)

        except Exception as e:
            error_msg = f"Completion stage error: {str(e)}"
            case_data = investigations.get(case_id)
            if case_data:
                case_data["status"] = "error"
                case_data["error"] = error_msg
                self._persist(case_id, investigations)
            log_audit(case_id, "STAGE_ERROR_COMPLETION", "AI_System", error_msg)
            await self.send_update(case_id, "error", f"❌ {error_msg}", progress=0)

    async def process_approval_decision(self, case_id: str, approval_id: str, decision: str, notes: str, investigations: dict, pending_approvals: dict):
        """Process human approval decision and continue investigation."""
        approval = pending_approvals.get(approval_id, {})
        action_type = approval.get("type", "")

        if decision == "approved":
            # Add to approved list
            if case_id in investigations:
                if "approvals" not in investigations[case_id]:
                    investigations[case_id]["approvals"] = []
                investigations[case_id]["approvals"].append({
                    "approval_id": approval_id,
                    "action": approval.get("action"),
                    "decision": decision,
                    "notes": notes,
                    "decided_at": datetime.now().isoformat()
                })
                self._persist(case_id, investigations)

            if action_type == "case_authorization":
                await self.send_update(case_id, "authorization_approved",
                    f"✅ Case authorized for investigation. Launching AI complaint analysis...", progress=5)
                log_audit(case_id, "CASE_AUTHORIZED", "officer", "Case authorized by officer")
                asyncio.create_task(
                    self.run_stage_complaint_analysis(case_id, investigations, pending_approvals)
                )

            elif action_type == "osint_approval":
                await self.send_update(case_id, "osint_approved",
                    f"✅ OSINT clearance approved. Initiating external lookups and transaction analysis...", progress=15)
                log_audit(case_id, "OSINT_CLEARANCE_APPROVED", "officer", "OSINT lookups authorized by officer")
                asyncio.create_task(
                    self.run_stage_analysis_and_banking(case_id, investigations, pending_approvals)
                )

            elif action_type == "bank_freeze":
                await self.send_update(case_id, "freeze_approved",
                    f"✅ Officer approved bank freeze. Preparing bank directives and network graph...", progress=55)
                log_audit(case_id, "FREEZE_APPROVED", "officer",
                         f"Bank freeze approved for {len(approval.get('details', []))} accounts")
                asyncio.create_task(
                    self.run_stage_reporting(case_id, investigations, pending_approvals)
                )

            elif action_type == "legal_escalation":
                await self.send_update(case_id, "escalation_approved",
                    f"✅ Legal escalation approved. Compiling BNS 2023 FIR drafts...", progress=85)
                log_audit(case_id, "ESCALATION_APPROVED", "officer", "Legal escalation approved")
                asyncio.create_task(
                    self.run_stage_generation(case_id, investigations, pending_approvals)
                )

            elif action_type == "final_signoff":
                await self.send_update(case_id, "signoff_approved",
                    f"✅ Final reports signed off. Finalizing investigation file...", progress=96)
                log_audit(case_id, "FINAL_SIGNOFF_APPROVED", "officer", "FIR and report signed off by officer")
                asyncio.create_task(
                    self.run_stage_complete(case_id, investigations)
                )

            elif action_type == "refund_authorization":
                amount_str = approval.get("meta", {}).get("amount", "0")
                try:
                    amount_val = float(amount_str.replace(",", ""))
                except:
                    amount_val = 0.0
                
                await self.send_update(case_id, "recovery_approved",
                    f"✅ Refund petition signed and authorized. Court order generated and funds released. Amount: Rs. {amount_str}", progress=100)
                log_audit(case_id, "RECOVERY_COMPLETED", "officer", f"Judicial release approved. Rs. {amount_str} returned to victim.")
                
                if case_id in investigations:
                    investigations[case_id]["recovery_status"] = "completed"
                    investigations[case_id]["recovered_amount"] = amount_val
                    self._persist(case_id, investigations)

        else:
            # Rejection or requested more info
            if case_id in investigations:
                if "approvals" not in investigations[case_id]:
                    investigations[case_id]["approvals"] = []
                investigations[case_id]["approvals"].append({
                    "approval_id": approval_id,
                    "action": approval.get("action"),
                    "decision": decision,
                    "notes": notes,
                    "decided_at": datetime.now().isoformat()
                })
                investigations[case_id]["status"] = "paused"
                self._persist(case_id, investigations)

            await self.send_update(case_id, "action_rejected",
                f"⚠️ Officer decision: {decision.upper()}. Details: {notes or 'No reason given'}. Pipeline paused.", progress=100)
            log_audit(case_id, f"APPROVAL_{decision.upper()}", "officer",
                     f"{approval.get('action')} — {notes or 'No details'}")
