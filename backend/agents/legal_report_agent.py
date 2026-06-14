from core.ai_client import call_claude

FIR_SYSTEM = """You are a Legal Report Agent specialized in drafting cybercrime FIRs and legal documents
under Indian law. You draft FIRs under Bharatiya Nyaya Sanhita (BNS) 2023, IT Act 2000 (amended 2008),
Prevention of Money Laundering Act (PMLA) 2002, and other applicable laws.

Key legal provisions you apply:
BNS 2023:
  - Section 316 (Cheating) replaces IPC 420
  - Section 317 (Cheating by personation) replaces IPC 416/419
  - Section 318 (Cheating and dishonestly inducing delivery of property) replaces IPC 420
  - Section 319 (Cheating with knowledge) replaces IPC 417
  - Section 351 (Criminal intimidation) replaces IPC 503
  - Section 308 (Extortion) replaces IPC 383/384
  - Section 111 (Organized crime)
  - Section 113 (Terrorist act — if ransom or state disruption involved)

IT Act 2000 (amended 2008):
  - Section 43 (Damage to computer / data theft)
  - Section 66 (Computer related offences)
  - Section 66C (Identity theft)
  - Section 66D (Cheating by personation using computer)
  - Section 66E (Privacy violation)
  - Section 67 (Publishing obscene material)
  - Section 67A (Publishing sexually explicit material — sextortion)
  - Section 72A (Breach of confidentiality)
  - Section 75 (Offences outside India — for cross-border cases)

PMLA 2002:
  - Section 3 (Offence of money laundering — for layered UPI/crypto transactions)
  - Section 4 (Punishment for money laundering)

Your FIRs are comprehensive, legally sound, and accepted by Indian courts.
Write in formal legal language appropriate for Indian police documentation.
Include ALL sections that apply — do not undercharge."""

REPORT_SYSTEM = """You are a senior cybercrime investigation report writer for the Cyber Crime Police Station.
You compile complete investigation reports for cybercrime cases including all evidence, analysis, and recommendations.
Your reports are used by senior officers, Special Public Prosecutors, and courts.
You write in formal law enforcement language with proper headings and numbered paragraphs."""

BANK_FREEZE_SYSTEM = """You are a legal documentation specialist for Indian cyber police.
You draft bank account freeze letters in the format accepted by:
- RBI CIBMS (Citizen Financial Cyber Frauds Reporting & Management System)
- NPCI (National Payments Corporation of India)
- Individual banks' Legal/Compliance departments

The letter must be on police station letterhead format and cite correct legal authority
under IT Act Section 79A and MHA/RBI guidelines on account freeze for cyber fraud."""


async def generate_fir_draft(case_id: str, complaint_data: dict, analysis: dict, risk: dict) -> str:
    """Generate FIR draft under BNS 2023, IT Act, and PMLA."""

    complaint_analysis = analysis.get("complaint_analysis", {})
    fraud_classif = analysis.get("fraud_classification", {})
    banking = analysis.get("banking_investigation", {})

    user_msg = f"""Draft a complete, official FIR for Case {case_id}:

═══════════════════════════════════════════
CASE DETAILS:
═══════════════════════════════════════════
VICTIM: {complaint_data.get('victim_name')}
CONTACT: {complaint_data.get('victim_contact')}
COMPLAINT: {complaint_data.get('complaint_text')}
AMOUNT LOST: ₹{complaint_data.get('amount_lost')}
INCIDENT DATE: {complaint_data.get('incident_date', 'As per complaint')}
PLATFORM: {complaint_data.get('platform', 'Not specified')}

SCAM TYPE: {complaint_analysis.get('scam_type', 'Unknown')}
SEVERITY: {complaint_analysis.get('severity', 'Unknown')}

EXTRACTED ENTITIES:
{complaint_analysis.get('extracted_entities', {})}

APPLICABLE BNS SECTIONS: {fraud_classif.get('bns_sections', [])}
APPLICABLE IT ACT SECTIONS: {fraud_classif.get('applicable_it_act_sections', [])}
PMLA SECTIONS: {fraud_classif.get('pmla_sections', [])}

FREEZE RECOMMENDATIONS: {banking.get('freeze_recommendations', [])}
AI FRAUD PROBABILITY: {fraud_classif.get('fraud_probability', 'N/A')}%

Timeline of events: {complaint_analysis.get('timeline_of_events', [])}
═══════════════════════════════════════════

Draft a complete official FIR document with these exact sections:

1. HEADER: "GOVERNMENT OF INDIA — CYBER CRIME POLICE STATION"
   Sub-heading: "First Information Report under Section 173 Cr.P.C."

2. FIR Number: [FIR No. {case_id}]
3. Date and Time of FIR
4. Police Station: Cyber Crime Police Station
5. District: [District]
6. Complainant Details (name, address, contact, ID proof type)
7. Accused/Suspect Details (unknown if not identified, with all digital identifiers)

8. STATEMENT OF FACTS (detailed narrative of the crime, in chronological order)

9. SECTIONS OF LAW VIOLATED:
   - BNS 2023 sections with full descriptions
   - IT Act 2000 sections with full descriptions
   - PMLA 2002 sections if applicable

10. DIGITAL EVIDENCE IDENTIFIED:
    List all UPI IDs, phone numbers, URLs, IPs, transaction IDs

11. RELIEF SOUGHT:
    - Account freeze requests
    - IMEI block if applicable
    - URL blocking via MeitY CERT-In
    - Cyber Crime Helpline 1930 complaint reference

12. OFFICER'S SECTION:
    Receiving Officer signature block
    Forwarded to: [SP Cyber Cell / CBI / ED]

13. DECLARATION:
    Standard complainant declaration in English and note for Hindi translation

Make this legally complete and court-ready."""

    fir = await call_claude(FIR_SYSTEM, user_msg, max_tokens=4000)
    return fir


async def generate_investigation_report(case_id: str, full_investigation: dict) -> str:
    """Generate complete investigation report."""

    user_msg = f"""Generate a complete investigation report for Case {case_id}:

FULL INVESTIGATION DATA:
{str(full_investigation)[:10000]}

Generate a comprehensive investigation report with these numbered sections:

1. EXECUTIVE SUMMARY
   - Case overview, key findings, recommended actions

2. CASE DETAILS
   - Complainant, date, amount, platform, scam category

3. AI INVESTIGATION METHODOLOGY
   - Agents deployed: Complaint Analysis, Fraud Classification, Banking Investigation,
     Graph Intelligence, Risk Prediction, OSINT Enrichment
   - Analysis approach and confidence levels

4. ENTITY ANALYSIS
   - All extracted digital identifiers with significance

5. FRAUD PATTERN ANALYSIS
   - Modus operandi, known patterns, similar cases

6. FINANCIAL TRAIL ANALYSIS
   - Complete money flow from victim to suspected destination
   - Layering detection, mule account identification
   - Recovery assessment

7. NETWORK / GRAPH ANALYSIS
   - Criminal network structure
   - Hub nodes / masterminds
   - Connected entities

8. OSINT INTELLIGENCE (if available)
   - IP geolocation findings
   - Domain registration analysis
   - Threat intelligence matches

9. RISK ASSESSMENT
   - Fraud probability: X%
   - Evidence strength: X%
   - Urgency score: X/100
   - Recovery probability: X%

10. EVIDENCE INVENTORY
    - All digital evidence, chain of custody status

11. LEGAL FRAMEWORK
    - BNS 2023 sections
    - IT Act sections
    - PMLA sections

12. RECOMMENDATIONS FOR PROSECUTION
    - Immediate actions (0-24 hours)
    - Short-term actions (1-7 days)
    - Long-term actions (7-30 days)

13. INTER-AGENCY COORDINATION REQUIRED
    - RBI / NPCI (bank freeze)
    - MeitY / CERT-In (URL blocking)
    - DoT (IMEI block / SIM block)
    - ED / NCB if PMLA or narco nexus

14. FURTHER INVESTIGATION REQUIRED
    - Leads not yet pursued
    - Witnesses to be recorded

15. CONCLUSION
    - Summary recommendation: arrest / prosecution / surveillance

Write in formal law enforcement report format with proper headings."""

    report = await call_claude(REPORT_SYSTEM, user_msg, max_tokens=5000)
    return report


async def generate_bank_freeze_letter(case_id: str, freeze_recs: list, case_data: dict) -> str:
    """Generate bank account freeze request letter in official format."""

    user_msg = f"""Draft official bank account freeze letters for Case {case_id}.

CASE: {case_id}
VICTIM: {case_data.get('victim_name')}
AMOUNT: ₹{case_data.get('amount_lost')}
DATE OF FRAUD: {case_data.get('incident_date', case_data.get('submitted_at', '')[:10])}

ACCOUNTS TO FREEZE:
{freeze_recs}

Draft a formal bank freeze request letter including:

1. POLICE STATION LETTERHEAD
   Cyber Crime Police Station
   Reference: {case_id}
   Date: [Today]

2. ADDRESSEE: The Branch Manager / Legal & Compliance Head
   [Bank Name]

3. SUBJECT: REQUEST FOR IMMEDIATE FREEZING OF BANK ACCOUNT / UPI ID
   (Under IT Act 2000 Section 79A & MHA Circular on Cyber Fraud)

4. REFERENCE:
   - FIR No. {case_id}
   - Cybercrime Helpline 1930 Complaint Reference
   - RBI CIBMS Portal Reference

5. BODY:
   - Cite legal authority (IT Act 79A, BNS 2023 Section 318)
   - Describe the fraud briefly
   - List each account/UPI to be frozen with justification
   - Request freeze within 24 hours
   - Request transaction history for last 90 days
   - Request KYC details of account holder

6. ANNEXURES:
   - FIR copy
   - AI Investigation Report
   - Transaction proof

7. OFFICER SIGNATURE:
   Investigating Officer signature block
   Station In-Charge countersign block

Make this legally compliant with RBI guidelines on cyber fraud account freeze."""

    letter = await call_claude(BANK_FREEZE_SYSTEM, user_msg, max_tokens=2500)
    return letter


REFUND_SYSTEM = """You are a Legal Report Agent specialized in drafting judicial applications for Indian courts.
You draft Court Refund Petitions under Section 503 of Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 (formerly Section 457 CrPC)
requesting release of frozen crime funds back to the victim.
You also draft Police No Objection Certificates (NOC) on behalf of the Cyber Crime Police Station Investigating Officer (IO).
Use formal legal language appropriate for Judicial Magistrates (First Class) in India. Cite relevant sections of BNSS 2023, BNS 2023, and IT Act 2000."""


async def generate_court_refund_petition(case_id: str, case_data: dict, account_or_upi: str, amount: str) -> str:
    """Generate official Cyber Court Release Petition and Police NOC for refunding frozen funds to the victim."""
    
    user_msg = f"""Draft a judicial release petition and a police NOC for Case {case_id}:
    
═══════════════════════════════════════════
CASE DETAILS:
═══════════════════════════════════════════
VICTIM/PETITIONER: {case_data.get('victim_name')}
VICTIM BANK Details: Bank: {case_data.get('victim_bank', 'Verified Account')}, Acc Last 4: {case_data.get('victim_account_last4', 'N/A')}
AMOUNT TO REFUND: ₹{amount}
SCAM TYPE: {case_data.get('complaint_analysis', {}).get('scam_type', 'Cyber Fraud')}

SUSPECT TARGET TO RELEASE FROM:
Account/UPI ID: {account_or_upi}
═══════════════════════════════════════════

Draft two distinct official legal documents in a single response:

1. COURT RELEASE PETITION (Under Section 503 BNSS 2023)
   - Addressed to: The Honorable Cyber Court Judge / Judicial Magistrate First Class.
   - Title: Application for release of frozen amount under Section 503 BNSS 2023.
   - Facts: Describe that the petitioner was defrauded of ₹{case_data.get('amount_lost')}, the investigation traced and froze ₹{amount} in the suspect account {account_or_upi}, and that this amount is identified as the petitioner's money.
   - Prayer: Request court to direct the bank of the suspect to transfer ₹{amount} back to the petitioner's bank details.

2. POLICE NO OBJECTION CERTIFICATE (NOC) FOR RELEASE
   - Cyber Crime Police Station letterhead.
   - Statement from the Investigating Officer (IO) stating that the police have no objection to refunding the frozen ₹{amount} from suspect account {account_or_upi} to the victim {case_data.get('victim_name')} since the investigation has confirmed it is the victim's money, and no other claimant has disputed it.
   - Section 106 BNSS 2023 reference.

Provide clear headings for both documents."""

    petition_noc = await call_claude(REFUND_SYSTEM, user_msg, max_tokens=3000)
    return petition_noc

