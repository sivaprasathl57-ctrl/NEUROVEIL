import datetime
from fpdf import FPDF

def sanitize_text(text: str) -> str:
    """Sanitize text to be Latin-1 compatible to prevent FPDF generation crashes."""
    if not text:
        return ""
    # Map common unicode characters to latin-1 approximations
    replacements = {
        "₹": "Rs.",
        "–": "-",  # en-dash
        "—": "-",  # em-dash
        "“": '"',  # curly double open quote
        "”": '"',  # curly double close quote
        "‘": "'",  # curly single open quote
        "’": "'",  # curly single close quote
        "•": "*",  # bullet point
        "…": "...", # ellipsis
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    
    # Encode to latin-1, replacing unsupported chars with '?'
    return text.encode('latin-1', 'replace').decode('latin-1')

class CyberInvestigationPDF(FPDF):
    def __init__(self, title_text="CYBER INVESTIGATION REPORT", is_fir=False):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.title_text = sanitize_text(title_text)
        self.is_fir = is_fir
        self.set_auto_page_break(auto=True, margin=20)
        self.alias_nb_pages() # Enables {nb} placeholder for total page count
        
    def header(self):
        # Draw background decoration border
        self.set_draw_color(30, 58, 95) # Navy Blue
        self.set_line_width(0.5)
        # Rect border on each page (8mm margins, A4 size: 210x297)
        self.rect(8, 8, 194, 281)
        
        # Header banner
        self.set_fill_color(13, 18, 36) # Slate dark blue
        self.rect(9, 9, 192, 22, 'F')
        
        self.set_xy(10, 11)
        self.set_text_color(0, 153, 255) # Light blue accent
        self.set_font("Helvetica", "B", 12)
        if self.is_fir:
            self.cell(0, 6, "POLICE DEPARTMENT - CYBER CRIME CELL", ln=True, align="C")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(245, 158, 11) # Warning gold
            self.cell(0, 4, "FIRST INFORMATION REPORT (DRAFT / CASE INTELLIGENCE)", ln=True, align="C")
        else:
            self.cell(0, 6, "AI CYBER CRIME INVESTIGATION SYSTEM v2.0", ln=True, align="C")
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(226, 232, 240)
            self.cell(0, 4, self.title_text, ln=True, align="C")
            
        self.ln(10)
        
    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}} - AI CYBER INVESTIGATION SYSTEM - STRICTLY CONFIDENTIAL", align="C")

    # Helper: Draw custom styled section headers
    def draw_section_title(self, title):
        self.ln(5)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(190, 7, f"  {sanitize_text(title).upper()}", ln=True, fill=True, align="L")
        self.ln(3)

    # Helper: Draw key-value row with lines
    def draw_key_value(self, key, value, key_width=50, height=6, bg=False):
        if bg:
            self.set_fill_color(248, 250, 252)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(71, 85, 105)
        self.cell(key_width, height, f" {sanitize_text(key)}:", border="B" if not bg else 0, fill=bg)
        
        self.set_font("Helvetica", "", 9)
        self.set_text_color(15, 23, 42)
        val_str = sanitize_text(str(value)) if value is not None else "N/A"
        self.cell(190 - key_width, height, f" {val_str}", border="B" if not bg else 0, ln=True, fill=bg)

    # Helper: Draw a grid metric card
    def draw_metric_card(self, x, y, width, height, label, value, color_rgb=(0, 102, 255)):
        self.set_draw_color(226, 232, 240)
        self.set_fill_color(248, 250, 252)
        self.rect(x, y, width, height, 'DF')
        
        self.set_xy(x + 2, y + 2)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(100, 116, 139)
        self.cell(width - 4, 4, sanitize_text(label).upper(), ln=True, align="C")
        
        self.set_xy(x + 2, y + 8)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color_rgb)
        self.cell(width - 4, 8, sanitize_text(str(value)), ln=True, align="C")
        
        self.set_fill_color(*color_rgb)
        self.rect(x, y + height - 2, width, 2, 'F')

    # Helper: Draw robust table with wrapping
    def draw_styled_table(self, headers, col_widths, rows):
        # Draw header
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        
        for i, h in enumerate(headers):
            align = "C" if i == 0 or h.lower() in ("amount", "step", "status", "priority") else "L"
            self.cell(col_widths[i], 8, f" {sanitize_text(h)}", border=1, fill=True, align=align)
        self.ln()
        
        # Draw rows
        self.set_text_color(15, 23, 42)
        self.set_font("Helvetica", "", 8)
        
        toggle_fill = False
        for row in rows:
            self.set_fill_color(248, 250, 252) if toggle_fill else self.set_fill_color(255, 255, 255)
            
            for i, val in enumerate(row):
                align = "C" if i == 0 or headers[i].lower() in ("amount", "step", "status", "priority") else "L"
                val_str = sanitize_text(str(val)) if val is not None else ""
                
                # Prevent layout breaks from overly long text
                max_chars = int(col_widths[i] / 1.6)
                if len(val_str) > max_chars and max_chars > 3:
                    val_str = val_str[:max_chars - 3] + "..."
                    
                self.cell(col_widths[i], 6, f" {val_str}", border=1, fill=True, align=align)
            self.ln()
            toggle_fill = not toggle_fill

def generate_fir_pdf(case_id: str, case_data: dict) -> bytes:
    """Generate official styled FIR Draft PDF and return binary bytes."""
    pdf = CyberInvestigationPDF(is_fir=True)
    pdf.add_page()
    pdf.ln(12)
    
    # Title Section
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 8, "FIRST INFORMATION REPORT (DRAFT)", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, "Generated automatically by AI Investigation Engine", ln=True, align="C")
    pdf.ln(5)
    
    # Metadata Box
    pdf.draw_section_title("Case Registration Details")
    pdf.draw_key_value("Case Reference ID", case_id, bg=True)
    pdf.draw_key_value("Complainant Name", case_data.get("victim_name"), bg=False)
    pdf.draw_key_value("Contact Details", case_data.get("victim_contact"), bg=True)
    pdf.draw_key_value("Offense Amount Involved", f"INR {case_data.get('amount_lost', '0')}", bg=False)
    
    submitted_at = case_data.get("submitted_at", "")
    if "T" in submitted_at:
        submitted_at = submitted_at.replace("T", " ")[:19]
    pdf.draw_key_value("Date & Time of Registration", submitted_at, bg=True)
    
    scam_type = case_data.get("complaint_analysis", {}).get("scam_type", "Unknown")
    pdf.draw_key_value("Classified Scam Type", str(scam_type).replace("_", " ").upper(), bg=False)
    
    # Legal sections
    bns = case_data.get("fraud_classification", {}).get("bns_sections", [])
    ipc = case_data.get("fraud_classification", {}).get("applicable_ipc_sections", [])
    it = case_data.get("fraud_classification", {}).get("applicable_it_act_sections", [])
    
    legal_parts = []
    if bns: legal_parts.append(", ".join(bns))
    if ipc: legal_parts.append(", ".join(ipc))
    if it: legal_parts.append(", ".join(it))
    
    legal_secs = ", ".join(legal_parts)
    pdf.draw_key_value("Applicable Legal Sections", legal_secs or "BNS Section 318, IT Act 66D", bg=True)
    pdf.ln(5)
    
    # FIR Draft Text
    pdf.draw_section_title("Statement of Facts (FIR Text)")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    
    fir_text = sanitize_text(case_data.get("fir_draft", "No FIR draft statement generated."))
    pdf.multi_cell(190, 5, fir_text, border=0, align="L")
    pdf.ln(15)
    
    # Signature Section
    if pdf.get_y() > 240:
        pdf.add_page()
        pdf.ln(12)
        
    y_sig = pdf.get_y()
    pdf.set_xy(10, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=False, align="C")
    pdf.set_xy(110, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=True, align="C")
    
    pdf.set_xy(10, y_sig + 6)
    pdf.cell(90, 5, "Signature / Thumb Impression of Complainant", ln=False, align="C")
    pdf.set_xy(110, y_sig + 6)
    pdf.cell(90, 5, "Investigating Officer (Cyber Crime Police Station)", ln=True, align="C")
    
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.set_xy(10, y_sig + 15)
    pdf.cell(0, 4, "*Note: This is an AI-generated draft FIR based on the cybercrime complaint. It serves as investigation intelligence.", ln=True, align="C")
    
    return bytes(pdf.output())

def generate_report_pdf(case_id: str, case_data: dict) -> bytes:
    """Generate official formatted Case Report PDF and return binary bytes."""
    pdf = CyberInvestigationPDF(title_text=f"CASE REPORT - {case_id}", is_fir=False)
    pdf.add_page()
    pdf.ln(12)
    
    # Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 8, "OFFICIAL CYBER CRIME INVESTIGATION REPORT", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 4, f"Case Reference: {case_id}", ln=True, align="C")
    pdf.ln(5)
    
    # Draw standard meta block
    pdf.draw_section_title("Incident Background")
    pdf.draw_key_value("Complainant Name", case_data.get("victim_name"))
    pdf.draw_key_value("Contact Info", case_data.get("victim_contact"), bg=True)
    pdf.draw_key_value("Total Financial Loss", f"INR {case_data.get('amount_lost')}")
    
    submitted_at = case_data.get("submitted_at", "")
    if "T" in submitted_at:
        submitted_at = submitted_at.replace("T", " ")[:19]
    pdf.draw_key_value("Submission Timestamp", submitted_at, bg=True)
    pdf.ln(5)
    
    # Narrative report text
    pdf.draw_section_title("Detailed Intelligence Findings")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    
    report_text = sanitize_text(case_data.get("investigation_report", "No investigation report text generated."))
    pdf.multi_cell(190, 5, report_text, border=0, align="L")
    pdf.ln(15)
    
    # Signatures
    if pdf.get_y() > 240:
        pdf.add_page()
        pdf.ln(12)
        
    y_sig = pdf.get_y()
    pdf.set_xy(10, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=False, align="C")
    pdf.set_xy(110, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=True, align="C")
    
    pdf.set_xy(10, y_sig + 6)
    pdf.cell(90, 5, "Cyber Cell Analyst Signature", ln=False, align="C")
    pdf.set_xy(110, y_sig + 6)
    pdf.cell(90, 5, "Authorizing Cyber Crime SP / ACP", ln=True, align="C")
    
    return bytes(pdf.output())

def generate_dossier_pdf(case_id: str, case_data: dict) -> bytes:
    """Generate a highly comprehensive Multi-Agent case dossier PDF containing all charts, scores, tables, and text drafts."""
    pdf = CyberInvestigationPDF(title_text=f"COMPLETE CASE DOSSIER - {case_id}", is_fir=False)
    pdf.add_page()
    pdf.ln(12)
    
    # ── COVER / HEADER ────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(13, 18, 36)
    pdf.cell(0, 10, "CYBERCRIME INTELLIGENCE DOSSIER", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 5, "INTEGRATED MULTI-AGENT FRAUD INTELLIGENCE REPORT", ln=True, align="C")
    pdf.ln(6)
    
    # Metrics Cards
    scores = case_data.get("final_scores") or case_data.get("risk_assessment", {}).get("overall_scores", {})
    fraud_prob = scores.get("fraud_probability") or case_data.get("fraud_classification", {}).get("fraud_probability", 0)
    evidence = scores.get("evidence_strength", 0)
    urgency = scores.get("urgency_score", 0)
    recovery = scores.get("recovery_probability", 0)
    net_risk = scores.get("network_risk", 0)
    
    y_start = pdf.get_y()
    pdf.draw_metric_card(10, y_start, 35, 18, "Fraud Prob.", f"{fraud_prob}%", (239, 68, 68))
    pdf.draw_metric_card(48, y_start, 35, 18, "Evidence Str.", f"{evidence}/100", (0, 153, 255))
    pdf.draw_metric_card(86, y_start, 35, 18, "Urgency", f"{urgency}/100", (245, 158, 11))
    pdf.draw_metric_card(124, y_start, 35, 18, "Recovery", f"{recovery}%", (34, 197, 94))
    pdf.draw_metric_card(162, y_start, 38, 18, "Network Risk", f"{net_risk}/100", (139, 92, 246))
    
    pdf.set_y(y_start + 24)
    
    # ── CASE SUMMARY ─────────────────────────────────────────────────────────
    pdf.draw_section_title("1. Case & Complainant Details")
    pdf.draw_key_value("Case Reference ID", case_id, bg=True)
    pdf.draw_key_value("Victim Name", case_data.get("victim_name"), bg=False)
    pdf.draw_key_value("Contact Details", case_data.get("victim_contact"), bg=True)
    pdf.draw_key_value("Amount Lost", f"INR {case_data.get('amount_lost', '0')}", bg=False)
    
    submitted_at = case_data.get("submitted_at", "")
    if "T" in submitted_at:
        submitted_at = submitted_at.replace("T", " ")[:19]
    pdf.draw_key_value("Submitted At", submitted_at, bg=True)
    
    scam_type = case_data.get("complaint_analysis", {}).get("scam_type", "Unknown")
    pdf.draw_key_value("Scam Classification", str(scam_type).replace("_", " ").upper(), bg=False)
    
    summary_text = sanitize_text(case_data.get("complaint_analysis", {}).get("summary", case_data.get("complaint_text", "")))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(50, 6, " Incident Summary Statement:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(190, 4.5, f" {summary_text}", border=0, align="L")
    
    # ── ENTITY SUMMARY ───────────────────────────────────────────────────────
    pdf.draw_section_title("2. Extracted Cyber Entities")
    entities = case_data.get("complaint_analysis", {}).get("extracted_entities", {})
    
    has_entities = False
    for category, values in entities.items():
        if values and len(values) > 0:
            has_entities = True
            val_str = ", ".join(values)
            pdf.draw_key_value(category.replace("_", " ").title(), val_str, bg=False)
            
    if not has_entities:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "No specific digital entities (UPI, Bank, URL, IP) extracted from statement.", ln=True)
        
    red_flags = case_data.get("complaint_analysis", {}).get("immediate_red_flags", [])
    if red_flags:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(239, 68, 68)
        pdf.cell(50, 5, " Immediate Red Flags Identified:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(127, 29, 29)
        for rf in red_flags:
            pdf.cell(0, 4.5, f" - {sanitize_text(rf)}", ln=True)

    # ── FRAUD ANALYSIS & LEGAL SECTIONS ───────────────────────────────────────
    pdf.draw_section_title("3. Fraud Pattern & Legal Classification")
    fraud = case_data.get("fraud_classification", {})
    pdf.draw_key_value("Modus Operandi Summary", fraud.get("modus_operandi", "N/A"))
    
    bns = fraud.get("bns_sections", [])
    ipc = fraud.get("applicable_ipc_sections", [])
    it = fraud.get("applicable_it_act_sections", [])
    legal_parts = []
    if bns: legal_parts.append(", ".join(bns))
    if ipc: legal_parts.append(", ".join(ipc))
    if it: legal_parts.append(", ".join(it))
    legal_secs = ", ".join(legal_parts)
    
    pdf.draw_key_value("Applicable Legal Statutes", legal_secs or "BNS Section 318, IT Act 66D", bg=True)
    
    # Suspect Profile
    profile = fraud.get("suspect_profile", {})
    if profile:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 5, " AI Suspect Profiling Details:", ln=True)
        pdf.draw_key_value("Org Level", profile.get("likely_organization"), key_width=40, bg=True)
        pdf.draw_key_value("Sophistication", profile.get("technical_sophistication"), key_width=40)
        pdf.draw_key_value("Geography", profile.get("geographic_indicators"), key_width=40, bg=True)
        pdf.draw_key_value("Suspect Count", profile.get("likely_number_of_suspects"), key_width=40)
        
    # ── FINANCIAL TRAIL ───────────────────────────────────────────────────────
    pdf.add_page() # Start financial on new page
    pdf.draw_section_title("4. Financial Transaction Trail Analysis")
    banking = case_data.get("banking_investigation", {})
    tx_chain = banking.get("transaction_analysis", {}).get("transaction_chain", [])
    
    if tx_chain:
        headers = ["Step", "From Account/UPI", "To Account/UPI", "Amount", "Method", "Account Type"]
        col_widths = [15, 40, 45, 25, 25, 40]
        rows = []
        for tx in tx_chain:
            rows.append([
                tx.get("step", ""),
                tx.get("from", ""),
                tx.get("to", ""),
                f"Rs. {tx.get('amount', '0')}",
                tx.get("method", ""),
                "Mule Account" if tx.get("is_mule_account") else str(tx.get("account_type", "")).replace("_", " ").title()
            ])
        pdf.draw_styled_table(headers, col_widths, rows)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, "No financial transaction chain available for display.", ln=True)
        
    # Freeze recommendations
    freezes = banking.get("freeze_recommendations", [])
    if freezes:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(220, 38, 38)
        pdf.cell(50, 5, " Recommended Bank Freeze Directives:", ln=True)
        pdf.ln(2)
        headers = ["Account/UPI Entity", "Associated Bank", "Priority", "Investigation Rationale"]
        col_widths = [45, 30, 25, 90]
        rows = []
        for fr in freezes:
            rows.append([
                fr.get("account_or_upi", ""),
                fr.get("bank", ""),
                fr.get("priority", "").upper(),
                fr.get("reason", "")
            ])
        pdf.draw_styled_table(headers, col_widths, rows)
        
    # ── RISK ASSESSMENT & ACTIONS ──────────────────────────────────────────────
    pdf.draw_section_title("5. Predictive Risk Assessment & Action Plan")
    risk = case_data.get("risk_assessment", {})
    
    actions = risk.get("priority_actions", [])
    if actions:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(50, 5, " Recommended Action Plan items:", ln=True)
        pdf.ln(2)
        headers = ["Action Required", "Assigned To", "Deadline", "Rationale"]
        col_widths = [50, 30, 30, 80]
        rows = []
        for act in actions:
            rows.append([
                act.get("action", ""),
                act.get("who", ""),
                act.get("deadline", ""),
                act.get("reason", "")
            ])
        pdf.draw_styled_table(headers, col_widths, rows)
        pdf.ln(3)

    timeline = risk.get("timeline_reconstruction", [])
    if timeline:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(50, 5, " Reconstructed Timeline of Events:", ln=True)
        pdf.ln(2)
        headers = ["Timestamp", "Reconstructed Incident Event", "Actor Involved", "Significance"]
        col_widths = [35, 75, 40, 40]
        rows = []
        for t in timeline:
            rows.append([
                t.get("timestamp", ""),
                t.get("event", ""),
                t.get("actor", ""),
                t.get("significance", "").title()
            ])
        pdf.draw_styled_table(headers, col_widths, rows)
        
    # ── ADVANCED INTEL (IF AVAILABLE) ───────────────────────────────────────
    adv = case_data.get("advanced_analysis", {})
    if adv and "note" not in adv:
        pdf.add_page()
        pdf.draw_section_title("6. Advanced Forensic Intelligence")
        
        # Behavioral Profiling
        beh = adv.get("behavioral_profile", {})
        if beh and isinstance(beh, dict) and "error" not in beh:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Suspect Behavioral Profile:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.draw_key_value("Scam Complexity Level", beh.get("complexity", "Medium"), key_width=50)
            pdf.draw_key_value("Suspect Motivation", beh.get("motivation", "Financial Gain"), key_width=50, bg=True)
            pdf.draw_key_value("Target Vulnerability Exploited", beh.get("target_vulnerability", "Trust/Urgency"), key_width=50)
            
            p_traits = beh.get("psychological_traits", [])
            if isinstance(p_traits, list):
                pdf.draw_key_value("Psychological Traits", ", ".join(p_traits), key_width=50, bg=True)
                
            obs = beh.get("modus_operandi_observations", [])
            if isinstance(obs, list) and obs:
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(50, 4, " Behavioral Observations:", ln=True)
                pdf.set_font("Helvetica", "", 8)
                for ob in obs:
                    pdf.cell(0, 4, f"  * {sanitize_text(ob)}", ln=True)
            pdf.ln(4)
            
        # Crypto Forensics
        crypto = adv.get("blockchain_forensics", {})
        if crypto and isinstance(crypto, dict) and "error" not in crypto:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Cryptocurrency Forensics & Blockchain Intelligence:", ln=True)
            
            pdf.draw_key_value("Crypto Address Identified", crypto.get("wallet_address", "N/A"), key_width=50)
            pdf.draw_key_value("Blockchain Network", crypto.get("blockchain_network", "Bitcoin (BTC)"), key_width=50, bg=True)
            pdf.draw_key_value("Wallet Balance", crypto.get("wallet_balance", "0.0 BTC"), key_width=50)
            pdf.draw_key_value("Total USD Traced", f"USD {crypto.get('total_usd_traced', '0')}", key_width=50, bg=True)
            
            hops = crypto.get("hops_traced", 0)
            pdf.draw_key_value("Hops Traced in Blockchain", str(hops), key_width=50)
            
            exchanges = crypto.get("off_ramps_detected", [])
            if isinstance(exchanges, list) and exchanges:
                pdf.draw_key_value("Exchange Off-Ramps Identified", ", ".join(exchanges), key_width=50, bg=True)
            pdf.ln(4)
            
        # Predictive escalation risk
        pred = adv.get("predictive_risk", {})
        if pred and isinstance(pred, dict) and "error" not in pred:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Escalation & Anomaly Projections:", ln=True)
            esc = pred.get("escalation_risk", {})
            pdf.draw_key_value("Escalation Risk Score", f"{esc.get('escalation_probability', 0)}% (Complexity: {esc.get('complexity_rating', 'low').upper()})", key_width=50)
            
            vulner = pred.get("victim_vulnerability", {})
            pdf.draw_key_value("Victim Vulnerability Index", f"{vulner.get('vulnerability_score', 0)}/100 (Type: {vulner.get('vulnerability_type', 'Standard')})", key_width=50, bg=True)
            
            fin = pred.get("financial_forecast", {})
            pdf.draw_key_value("Forecasted Financial Exposure", f"INR {fin.get('forecasted_loss', 0)} (Risk Rating: {fin.get('vulnerability_score', 'medium').upper()})", key_width=50)
            pdf.ln(4)
            
        # IOCs
        iocs = adv.get("iocs", {})
        if iocs and isinstance(iocs, dict) and "error" not in iocs:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Indicators of Compromise (IOC) Export Registry:", ln=True)
            
            all_iocs = []
            for t, vals in iocs.get("iocs", {}).items():
                if vals:
                    all_iocs.append(f"{t.upper()}: {', '.join(vals)}")
            if all_iocs:
                pdf.set_font("Helvetica", "", 8)
                for item in all_iocs:
                    pdf.multi_cell(190, 4, f"  * {sanitize_text(item)}", border=0, align="L")
            else:
                pdf.set_font("Helvetica", "I", 8)
                pdf.cell(0, 4, "  No technical IOCs registry found.", ln=True)
            pdf.ln(4)

    # ── OSINT ENRICHMENT FINDINGS (IF AVAILABLE) ──────────────────────────────
    osint = case_data.get("osint_enrichment") or case_data.get("advanced_analysis", {}).get("osint", {})
    if osint and isinstance(osint, dict) and (osint.get("summary") or osint.get("ip_analysis") or osint.get("domain_analysis") or osint.get("phone_analysis")):
        pdf.add_page()
        pdf.draw_section_title("7. OSINT Enrichment Findings")
        
        summary = osint.get("summary", {})
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 6, "OSINT Summary & Key Indicators:", ln=True)
        pdf.draw_key_value("Threat Level", str(summary.get("threat_level", "unknown")).upper(), key_width=60)
        pdf.draw_key_value("Total Indicators Checked", str(summary.get("total_indicators", 0)), key_width=60, bg=True)
        pdf.draw_key_value("Malicious URLs Detected", str(summary.get("malicious_urls", 0)), key_width=60)
        pdf.draw_key_value("Foreign IPs Detected", str(summary.get("foreign_ips", 0)), key_width=60, bg=True)
        pdf.draw_key_value("Suspicious Domains Detected", str(summary.get("suspicious_domains", 0)), key_width=60)
        pdf.ln(4)
        
        # IP Geolocation Table
        ip_analysis = osint.get("ip_analysis", [])
        if ip_analysis:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "IP Geolocation Details:", ln=True)
            pdf.ln(1)
            headers = ["IP Address", "Country", "Region/City", "ISP/Organization", "VPN Likely"]
            col_widths = [35, 30, 40, 65, 20]
            rows = []
            for ip in ip_analysis:
                rows.append([
                    ip.get("ip", "N/A"),
                    ip.get("country", "Unknown"),
                    f"{ip.get('region', '')}/{ip.get('city', '')}",
                    ip.get("isp", "Unknown"),
                    "YES" if ip.get("is_vpn_likely") else "NO"
                ])
            pdf.draw_styled_table(headers, col_widths, rows)
            pdf.ln(4)
            
        # Domain WHOIS Table
        domain_analysis = osint.get("domain_analysis", [])
        if domain_analysis:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Domain WHOIS details:", ln=True)
            pdf.ln(1)
            headers = ["Domain", "Registrar", "Registered Date", "Expires Date", "Newly Reg (<90d)"]
            col_widths = [45, 55, 30, 30, 30]
            rows = []
            for dom in domain_analysis:
                rows.append([
                    dom.get("domain", "N/A"),
                    dom.get("registrar", "Unknown"),
                    dom.get("registered", "Unknown"),
                    dom.get("expires", "Unknown"),
                    "YES" if dom.get("is_newly_registered") else "NO"
                ])
            pdf.draw_styled_table(headers, col_widths, rows)
            pdf.ln(4)

        # Phone Analysis Table
        phone_analysis = osint.get("phone_analysis", [])
        if phone_analysis:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Phone Intelligence:", ln=True)
            pdf.ln(1)
            headers = ["Phone Number", "Country", "Carrier Hint", "Is Mobile", "Observations"]
            col_widths = [35, 25, 45, 20, 65]
            rows = []
            for ph in phone_analysis:
                obs_list = ph.get("notes", [])
                obs_str = "; ".join(obs_list) if obs_list else "Normal range"
                rows.append([
                    ph.get("phone", "N/A"),
                    ph.get("country", "Unknown"),
                    ph.get("carrier_hint", "Unknown"),
                    "YES" if ph.get("is_mobile") else "NO",
                    obs_str
                ])
            pdf.draw_styled_table(headers, col_widths, rows)
            pdf.ln(4)

    # ── EVIDENCE CHAIN OF CUSTODY ─────────────────────────────────────────────
    evidence_list = case_data.get("evidence", [])
    custody_log = case_data.get("custody_log", [])
    if evidence_list or custody_log:
        pdf.add_page()
        pdf.draw_section_title("8. Digital Evidence Inventory & Chain of Custody")
        
        if evidence_list:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Inventory of Admissible Digital Evidence:", ln=True)
            pdf.ln(1)
            headers = ["ID", "Filename", "File Type", "Size (Bytes)", "SHA-256 Hash"]
            col_widths = [12, 55, 33, 25, 65]
            rows = []
            for ev in evidence_list:
                rows.append([
                    str(ev.get("id", "")),
                    ev.get("file_name", "N/A"),
                    ev.get("file_type", "Unknown"),
                    str(ev.get("file_size", 0)),
                    ev.get("sha256_hash", "N/A")
                ])
            pdf.draw_styled_table(headers, col_widths, rows)
            pdf.ln(4)
            
        if custody_log:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(30, 58, 95)
            pdf.cell(0, 6, "Chain of Custody Audit Log (Sec. 63 BSA 2023):", ln=True)
            pdf.ln(1)
            headers = ["Timestamp", "Evidence ID", "Action", "Actor", "Details"]
            col_widths = [38, 22, 25, 30, 75]
            rows = []
            for log in custody_log:
                ts_str = log.get("timestamp", "")
                if "T" in ts_str:
                    ts_str = ts_str.replace("T", " ")[:19]
                rows.append([
                    ts_str,
                    f"EV-{log.get('evidence_id', 'N/A')}",
                    log.get("action", ""),
                    log.get("actor", ""),
                    log.get("details", "")
                ])
            pdf.draw_styled_table(headers, col_widths, rows)
            pdf.ln(4)

    # ── BANK FREEZE REQUEST LETTER (ANNEXURE) ─────────────────────────────────
    freeze_letter = case_data.get("bank_freeze_letter")
    if freeze_letter:
        pdf.add_page()
        pdf.draw_section_title("9. Annexure: Bank Account Freeze Request")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(190, 5, sanitize_text(freeze_letter), border=0, align="L")
        pdf.ln(10)

    # ── GENERATED REPORTS ────────────────────────────────────────────────────
    pdf.add_page()
    pdf.draw_section_title("10. Official FIR Draft Statement")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    fir_text = sanitize_text(case_data.get("fir_draft", "No FIR statement generated."))
    pdf.multi_cell(190, 5, fir_text, border=0, align="L")
    pdf.ln(10)
    
    pdf.add_page()
    pdf.draw_section_title("11. Detailed Investigation Narrative Report")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    report_text = sanitize_text(case_data.get("investigation_report", "No narrative investigation report text generated."))
    pdf.multi_cell(190, 5, report_text, border=0, align="L")
    pdf.ln(15)
    
    # ── SIGNATURES ──────────────────────────────────────────────────────────
    if pdf.get_y() > 240:
        pdf.add_page()
        pdf.ln(12)
        
    y_sig = pdf.get_y()
    pdf.set_xy(10, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=False, align="C")
    pdf.set_xy(110, y_sig)
    pdf.cell(90, 5, "___________________________________", ln=True, align="C")
    
    pdf.set_xy(10, y_sig + 6)
    pdf.cell(90, 5, "Lead Cyber Forensic Investigator", ln=False, align="C")
    pdf.set_xy(110, y_sig + 6)
    pdf.cell(90, 5, "Officer-in-Charge / Cyber Superintendent", ln=True, align="C")
    
    return bytes(pdf.output())


def _draw_court_letterhead(pdf):
    """Draw official police station letterhead banner."""
    # Top Banner — dark navy government color
    pdf.set_fill_color(13, 28, 64)
    pdf.rect(9, 9, 192, 30, 'F')
    
    # Left accent bar (saffron/govt color)
    pdf.set_fill_color(255, 153, 0)
    pdf.rect(9, 9, 4, 30, 'F')
    
    # Right accent bar (green/govt color)
    pdf.set_fill_color(19, 136, 8)
    pdf.rect(197, 9, 4, 30, 'F')
    
    # Letterhead text
    pdf.set_xy(14, 11)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(183, 6, "CYBER CRIME POLICE STATION", ln=True, align="C")
    
    pdf.set_xy(14, 18)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(183, 5, "Ministry of Home Affairs, Government of India", ln=True, align="C")
    
    pdf.set_xy(14, 24)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 200, 50)
    pdf.cell(183, 5, "National Cyber Crime Reporting Portal | Helpline: 1930", ln=True, align="C")
    
    # Bottom strip of banner
    pdf.set_fill_color(0, 80, 200)
    pdf.rect(9, 36, 192, 2, 'F')
    
    pdf.set_y(45)


def generate_refund_petition_pdf(case_id: str, case_data: dict) -> bytes:
    """Generate a professional Court Release Petition (Sec 503 BNSS 2023) and Police NOC PDF."""
    from fpdf import FPDF
    import datetime as dt
    
    today = dt.datetime.now().strftime("%d %B %Y")
    time_now = dt.datetime.now().strftime("%H:%M hrs")
    
    # Use a plain FPDF so we can fully control the layout
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()

    # ═══════════════════════════════════════════════════
    # PAGE 1 — COURT RELEASE PETITION
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    
    # Outer border
    pdf.set_draw_color(13, 28, 64)
    pdf.set_line_width(0.8)
    pdf.rect(8, 8, 194, 281)
    pdf.set_line_width(0.3)
    pdf.rect(10, 10, 190, 277)
    
    # Letterhead
    _draw_court_letterhead(pdf)
    
    # Document Title
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(0, 8, "APPLICATION FOR RELEASE OF FROZEN AMOUNT", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(180, 20, 20)
    pdf.cell(0, 6, "Under Section 503, Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023", ln=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "(Formerly Section 457, Code of Criminal Procedure 1973)", ln=True, align="C")
    pdf.ln(3)
    
    # Reference block
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(100, 140, 220)
    pdf.rect(12, pdf.get_y(), 186, 20, 'DF')
    y0 = pdf.get_y() + 3
    pdf.set_xy(14, y0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 58, 120)
    pdf.cell(60, 5, f"Case Reference No.: {sanitize_text(case_id)}", ln=False)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(60, 5, f"Date: {today}", ln=False)
    pdf.cell(60, 5, f"Time: {time_now}", ln=True)
    pdf.set_xy(14, y0 + 7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 58, 120)
    pdf.cell(60, 5, f"FIR No.: {sanitize_text(case_id)}", ln=False)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(90, 5, "Police Station: Cyber Crime Police Station", ln=True)
    pdf.set_y(pdf.get_y() + 5)
    
    # Addressed To
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(0, 6, "TO,", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(100, 0, 0)
    pdf.cell(0, 6, "THE HONOURABLE JUDICIAL MAGISTRATE (FIRST CLASS)", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 5, "Cyber Court / District & Sessions Court", ln=True)
    pdf.ln(3)
    
    # Subject
    pdf.set_fill_color(255, 245, 200)
    pdf.set_draw_color(200, 160, 0)
    pdf.rect(12, pdf.get_y(), 186, 10, 'DF')
    pdf.set_xy(14, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 60, 0)
    amount_str = sanitize_text(str(case_data.get('recovered_amount', 0)))
    victim_name = sanitize_text(str(case_data.get('victim_name', 'Unknown Victim')))
    pdf.cell(0, 6, f"SUBJECT: Application for Release of Frozen Amount of Rs. {amount_str} to Victim {victim_name}", ln=True)
    pdf.set_y(pdf.get_y() + 3)
    
    # Petitioner Info Section
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  SECTION A: PETITIONER DETAILS", ln=True, fill=True)
    pdf.ln(2)
    
    def kv(label, val, alt=False):
        if alt:
            pdf.set_fill_color(245, 248, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(60, 80, 130)
        pdf.cell(55, 6, f"  {label}:", border="B", fill=alt)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(135, 6, f"  {sanitize_text(str(val)) if val else 'N/A'}", border="B", fill=alt, ln=True)
    
    kv("Full Name of Petitioner", case_data.get('victim_name'), False)
    kv("Contact / Mobile Number", case_data.get('victim_contact'), True)
    kv("Victim Bank Name", case_data.get('victim_bank', 'As per complaint record'), False)
    kv("Account No. (Last 4 digits)", case_data.get('victim_account_last4', 'XXXX'), True)
    kv("Amount Originally Lost", f"Rs. {case_data.get('amount_lost', '0')} (Reported)", False)
    kv("Amount Traced & Frozen", f"Rs. {case_data.get('recovered_amount', '0')} (Identified)", True)
    kv("Date of Incident", case_data.get('incident_date', case_data.get('submitted_at', '')[:10] if case_data.get('submitted_at') else 'As per FIR'), False)
    pdf.ln(4)
    
    # Prayer / Statement Section
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  SECTION B: AI-DRAFTED PETITION & PRAYER", ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(20, 20, 20)
    
    petition_text = case_data.get("refund_petition_draft", "")
    if not petition_text:
        petition_text = (
            f"The petitioner {case_data.get('victim_name', 'victim')} was defrauded through cybercrime "
            f"resulting in loss of Rs.{case_data.get('amount_lost', '0')}. The investigation conducted by "
            f"the Cyber Crime Police Station under FIR No. {case_id} has traced and frozen "
            f"Rs.{case_data.get('recovered_amount', '0')} in the suspect account. "
            f"The petitioner prays that this Honourable Court may be pleased to direct the concerned "
            f"bank to release the frozen amount of Rs.{case_data.get('recovered_amount', '0')} "
            f"to the petitioner as the rightful owner, as established by the investigation report."
        )
    
    petition_text_clean = sanitize_text(petition_text)
    pdf.multi_cell(190, 5, petition_text_clean, border=0, align="J")
    pdf.ln(3)
    
    # PRAYER BOX
    pdf.set_fill_color(230, 255, 230)
    pdf.set_draw_color(0, 160, 0)
    pdf.rect(12, pdf.get_y(), 186, 16, 'DF')
    pdf.set_xy(14, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 5, "PRAYER:", ln=True)
    pdf.set_xy(14, pdf.get_y())
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(20, 60, 20)
    pdf.cell(0, 5, f"Direct the bank to release Rs. {amount_str} from the frozen suspect account(s) back to the petitioner {victim_name}.", ln=True)
    pdf.set_y(pdf.get_y() + 3)
    
    # Signature section
    if pdf.get_y() > 240:
        pdf.add_page()
        # Redraw border on new page
        pdf.set_draw_color(13, 28, 64)
        pdf.set_line_width(0.8)
        pdf.rect(8, 8, 194, 281)
        pdf.set_line_width(0.3)
        pdf.rect(10, 10, 190, 277)
    
    pdf.ln(8)
    y_sig = pdf.get_y()
    
    pdf.set_xy(12, y_sig)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(90, 5, "Respectfully submitted,", ln=False)
    pdf.set_xy(110, y_sig)
    pdf.cell(90, 5, "Verified by:", ln=True)
    
    pdf.set_xy(12, y_sig + 12)
    pdf.cell(90, 5, "__________________________________", ln=False)
    pdf.set_xy(110, y_sig + 12)
    pdf.cell(90, 5, "__________________________________", ln=True)
    
    pdf.set_xy(12, y_sig + 18)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(90, 5, f"Petitioner: {victim_name}", ln=False)
    pdf.set_xy(110, y_sig + 18)
    pdf.cell(90, 5, "Investigating Officer", ln=True)
    
    pdf.set_xy(12, y_sig + 24)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(90, 5, f"Date: {today}", ln=False)
    pdf.set_xy(110, y_sig + 24)
    pdf.cell(90, 5, "Cyber Crime Police Station", ln=True)
    
    # Footer note
    pdf.set_y(-25)
    pdf.set_fill_color(13, 28, 64)
    pdf.rect(9, pdf.get_y(), 192, 8, 'F')
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(180, 200, 255)
    pdf.cell(0, 8, f"  Case Ref: {sanitize_text(case_id)}  |  Generated by AI Cyber Investigation System  |  Page 1/{{nb}}  |  STRICTLY CONFIDENTIAL", align="C")
    
    # ═══════════════════════════════════════════════════
    # PAGE 2 — POLICE NO OBJECTION CERTIFICATE
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    
    # Outer border
    pdf.set_draw_color(13, 28, 64)
    pdf.set_line_width(0.8)
    pdf.rect(8, 8, 194, 281)
    pdf.set_line_width(0.3)
    pdf.rect(10, 10, 190, 277)
    
    # Letterhead
    _draw_court_letterhead(pdf)
    
    # NOC Title
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(0, 8, "POLICE NO OBJECTION CERTIFICATE", ln=True, align="C")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(100, 0, 0)
    pdf.cell(0, 5, "(For Release of Frozen Cybercrime Funds Under Section 106, BNSS 2023)", ln=True, align="C")
    pdf.ln(4)
    
    # NOC Reference block
    pdf.set_fill_color(245, 245, 255)
    pdf.set_draw_color(100, 100, 200)
    pdf.rect(12, pdf.get_y(), 186, 22, 'DF')
    y0 = pdf.get_y() + 3
    pdf.set_xy(14, y0)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(90, 5, f"NOC Reference No.: NOC-{sanitize_text(case_id)}", ln=False)
    pdf.cell(90, 5, f"Date of Issue: {today}", ln=True)
    pdf.set_xy(14, y0 + 7)
    pdf.cell(90, 5, f"FIR / Case No.: {sanitize_text(case_id)}", ln=False)
    pdf.cell(90, 5, "Issuing Authority: Cyber Crime Police Station", ln=True)
    pdf.set_xy(14, y0 + 14)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 5, "Under: IT Act 2000 (Sec 79A), BNSS 2023 (Sec 106), MHA Guidelines on Cyber Fraud Account Freeze", ln=True)
    pdf.set_y(pdf.get_y() + 5)
    
    # NOC Body
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(190, 7, "  THIS IS TO CERTIFY THAT:", ln=True, fill=True)
    pdf.ln(3)
    
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(20, 20, 20)
    
    scam_type = str(case_data.get('complaint_analysis', {}).get('scam_type', 'Cyber Fraud')).replace('_', ' ').title()
    
    noc_body = (
        f"1.  This Cyber Crime Police Station registered Case No. {case_id} based on a cybercrime complaint "
        f"filed by {case_data.get('victim_name', 'the victim')} regarding a {scam_type} offence resulting "
        f"in a financial loss of Rs. {case_data.get('amount_lost', 'N/A')}.\n\n"
        f"2.  In the course of investigation conducted under the Bharatiya Nyaya Sanhita (BNS) 2023, "
        f"the Information Technology Act 2000 (amended 2008), and the BNSS 2023, the Investigating Officer "
        f"traced and identified the proceeds of crime amounting to Rs. {case_data.get('recovered_amount', '0')} "
        f"in the suspect account(s), which were subsequently frozen under Section 106, BNSS 2023.\n\n"
        f"3.  The investigation has conclusively established that the said amount of Rs. {case_data.get('recovered_amount', '0')} "
        f"rightfully belongs to the victim/petitioner and is not subject to any further dispute, legal claim, "
        f"or ongoing enforcement action by this Police Station.\n\n"
        f"4.  This Police Station DOES NOT OBJECT to the release of Rs. {case_data.get('recovered_amount', '0')} "
        f"from the frozen suspect account(s) to the rightful owner/petitioner {case_data.get('victim_name', 'victim')} "
        f"as per the order of the Honourable Court.\n\n"
        f"5.  This NOC is issued without prejudice to any other proceedings or recoveries that may be "
        f"required in relation to the above-mentioned cybercrime case."
    )
    
    pdf.multi_cell(190, 5.5, sanitize_text(noc_body), border=0, align="J")
    pdf.ln(5)
    
    # Legal declaration box
    pdf.set_fill_color(255, 245, 200)
    pdf.set_draw_color(200, 150, 0)
    pdf.set_line_width(0.5)
    pdf.rect(12, pdf.get_y(), 186, 18, 'DF')
    pdf.set_xy(14, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 60, 0)
    pdf.cell(0, 5, "DECLARATION UNDER SECTION 193 BNS 2023:", ln=True)
    pdf.set_xy(14, pdf.get_y())
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(60, 40, 0)
    pdf.multi_cell(182, 4.5, sanitize_text(
        "I, the Investigating Officer, do hereby certify on my honour and conscience that the above facts "
        "are true and correct to the best of my knowledge and belief. This certificate is issued in good "
        "faith and in the interest of justice for return of fraudulently obtained funds to the rightful victim."
    ), border=0, align="J")
    pdf.set_y(pdf.get_y() + 5)
    
    # Signature section
    y_sig = pdf.get_y()
    if y_sig > 240:
        pdf.add_page()
        pdf.set_draw_color(13, 28, 64)
        pdf.set_line_width(0.8)
        pdf.rect(8, 8, 194, 281)
        y_sig = 20
    
    pdf.ln(6)
    y_sig = pdf.get_y()
    
    # Two signature blocks
    pdf.set_xy(12, y_sig + 10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(85, 5, "__________________________________", ln=False)
    pdf.set_xy(110, y_sig + 10)
    pdf.cell(88, 5, "__________________________________", ln=True)
    
    pdf.set_xy(12, y_sig + 16)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(85, 5, "Investigating Officer (IO)", ln=False)
    pdf.set_xy(110, y_sig + 16)
    pdf.cell(88, 5, "Station House Officer (SHO)", ln=True)
    
    pdf.set_xy(12, y_sig + 22)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(85, 4, "Cyber Crime Police Station", ln=False)
    pdf.set_xy(110, y_sig + 22)
    pdf.cell(88, 4, "Cyber Crime Police Station", ln=True)
    
    pdf.set_xy(12, y_sig + 27)
    pdf.cell(85, 4, f"Date: {today}", ln=False)
    pdf.set_xy(110, y_sig + 27)
    pdf.cell(88, 4, f"Date: {today}", ln=True)
    
    # Seal placeholder
    pdf.set_draw_color(13, 28, 64)
    pdf.set_line_width(0.5)
    pdf.ellipse(155, y_sig, 30, 20)
    pdf.set_xy(148, y_sig + 6)
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_text_color(13, 28, 64)
    pdf.cell(30, 4, "OFFICIAL SEAL", ln=True, align="C")
    pdf.set_xy(148, y_sig + 10)
    pdf.set_font("Helvetica", "", 5)
    pdf.cell(30, 3, "CYBER CRIME POLICE", ln=True, align="C")
    
    # Footer note
    pdf.set_y(-25)
    pdf.set_fill_color(13, 28, 64)
    pdf.rect(9, pdf.get_y(), 192, 8, 'F')
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(180, 200, 255)
    pdf.cell(0, 8, f"  Case Ref: {sanitize_text(case_id)}  |  AI Cyber Investigation System  |  Page 2/{{nb}}  |  CONFIDENTIAL - FOR COURT USE ONLY", align="C")
    
    return bytes(pdf.output())

