from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are an expert Cybercrime Complaint Analysis Agent for Indian law enforcement.
You analyze cybercrime complaints and extract all digital evidence entities.
You are part of a multi-agent AI investigation system used by cyber police officers.

You are aware of all major cybercrime patterns in India including:
- UPI/Banking fraud, phishing, impersonation of banks/government/police
- Investment fraud (fake stock tips, crypto scams, Ponzi)
- Sextortion and online blackmail
- SIM swap fraud and OTP bypass
- Loan app fraud and recovery harassment
- Job/internship fraud
- Romance scam / matrimonial fraud
- TRAI/DoT/UIDAI impersonation (threatening fake disconnection)
- FedEx/Courier parcel scam (fake customs officials)
- Deepfake/AI voice fraud (impersonation using AI)
- APK malware / remote access trojans (AnyDesk, TeamViewer abuse)
- Crypto investment scams (pig butchering)
- Mule account recruitment
- Online marketplace fraud (OLX, Facebook marketplace)
- WhatsApp/Telegram group scams
- Ransomware attacks on businesses/hospitals
- Cyber stalking, trolling, defamation

Always think like a senior cybercrime investigator. Be thorough, precise, and look for hidden patterns.
Extract EVERY digital identifier — phones, UPIs, emails, IPs, URLs, accounts, IMEI numbers, social handles."""


async def analyze_complaint(complaint_data: dict) -> dict:
    """Extract entities and classify the cybercrime complaint."""

    user_msg = f"""Analyze this cybercrime complaint and extract all entities:

COMPLAINT TEXT: {complaint_data.get('complaint_text', '')}
VICTIM NAME: {complaint_data.get('victim_name', '')}
VICTIM CONTACT: {complaint_data.get('victim_contact', '')}
TRANSACTION IDs: {complaint_data.get('transaction_ids', '')}
UPI IDs: {complaint_data.get('upi_ids', '')}
SUSPECT PHONES: {complaint_data.get('suspect_phones', '')}
SUSPECT EMAILS: {complaint_data.get('suspect_emails', '')}
URLS: {complaint_data.get('urls', '')}
AMOUNT LOST: ₹{complaint_data.get('amount_lost', '0')}
INCIDENT DATE: {complaint_data.get('incident_date', '')}
INCIDENT TIME: {complaint_data.get('incident_time', '')}
PLATFORM USED: {complaint_data.get('platform', '')}
DEVICE TYPE: {complaint_data.get('device_type', '')}

Return a JSON object with:
{{
  "extracted_entities": {{
    "phone_numbers": ["list of ALL phone numbers found"],
    "whatsapp_numbers": ["WhatsApp numbers specifically"],
    "upi_ids": ["list of UPI IDs"],
    "bank_accounts": ["list of account numbers"],
    "ifsc_codes": ["IFSC codes"],
    "ip_addresses": ["list of IPs if any"],
    "urls": ["list of URLs / fake websites"],
    "email_addresses": ["list of emails"],
    "social_media_handles": ["Facebook/Instagram/Twitter handles"],
    "crypto_wallets": ["list of crypto addresses"],
    "transaction_ids": ["list of transaction IDs / UTR numbers"],
    "suspect_names": ["list of suspect names or aliases"],
    "imei_numbers": ["IMEI numbers if mentioned"],
    "app_names": ["apps used: AnyDesk, TeamViewer, etc."],
    "government_ids_claimed": ["fake officer badge numbers, etc."]
  }},
  "scam_type": "one of: investment_fraud | phishing | impersonation_bank | impersonation_govt | impersonation_police | sextortion | loan_app_fraud | crypto_scam | mule_account_fraud | apk_malware | job_fraud | romance_scam | sim_swap | otp_fraud | fedex_courier_scam | trai_impersonation | deepfake_fraud | marketplace_fraud | ransomware | cyber_stalking | other",
  "scam_type_reason": "brief explanation why this classification",
  "severity": "critical | high | medium | low",
  "amount_involved": "numeric amount in INR",
  "summary": "2-3 sentence case summary for the FIR",
  "key_observations": ["list of 4-6 important observations from the complaint"],
  "immediate_red_flags": ["list of immediate red flags found"],
  "victim_vulnerability_factors": ["factors that made victim susceptible"],
  "timeline_of_events": [
    {{"time": "approximate time", "event": "what happened", "actor": "victim | suspect | unknown"}}
  ],
  "likely_crime_gang": "individual | small_gang | organized_syndicate | unknown",
  "cross_border_likely": true or false,
  "digital_evidence_available": ["types of evidence victim may have: screenshots, call recordings, bank statements, etc."]
}}"""

    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
