from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are a Fraud Classification and Pattern Recognition Agent specializing in Indian cybercrime.
You have deep knowledge of:
- UPI fraud, digital arrest scams, investment fraud, pig butchering
- OTP fraud, SIM swap attacks, TRAI/DoT impersonation
- FedEx/courier parcel scams, fake customs officer scams
- Fake loan app frauds, recovery harassment
- Mule account networks, layering and smurfing
- Crypto scam operations, cold wallet drains
- APK malware, AnyDesk/TeamViewer RAT abuse
- Deepfake/AI voice fraud for impersonation
- Sextortion, blackmail, online grooming
- Marketplace fraud (OLX, Quikr, Facebook)
- Job/internship/work-from-home fraud
- SIM swap, account takeover, credential stuffing

You apply Bharatiya Nyaya Sanhita (BNS) 2023, IT Act 2000, and PMLA 2002.
You know which sections replace the old IPC sections.
You identify money laundering patterns requiring PMLA action.
You correlate patterns across multiple cases and identify fraud networks."""


async def classify_fraud(case_id: str, entities: dict, complaint_text: str, amount: str) -> dict:
    """Perform deep fraud classification and pattern analysis."""

    user_msg = f"""Perform deep fraud classification for Case {case_id}:

EXTRACTED ENTITIES: {entities}
COMPLAINT: {complaint_text}
AMOUNT LOST: ₹{amount}

Analyze and return JSON:
{{
  "fraud_probability": <0-100 integer>,
  "risk_score": <0-100 integer>,
  "evidence_confidence": <0-100 integer>,
  "urgency_score": <0-100 integer>,
  "fraud_patterns_detected": [
    {{
      "pattern": "pattern name",
      "description": "how this pattern appears in this case",
      "confidence": <0-100>
    }}
  ],
  "money_flow_analysis": {{
    "entry_point": "how victim was contacted/targeted",
    "payment_method": "UPI/Bank Transfer/Crypto/IMPS/RTGS etc",
    "suspected_layering": true or false,
    "layering_stages": <number of suspected layers>,
    "flow_description": "describe the suspected money movement path",
    "final_destination_likely": "crypto | cash | foreign account | still in Indian banking",
    "recovery_possibility": "high | medium | low | very_low",
    "recovery_window": "immediate | 24hrs | 72hrs | 7days | unlikely"
  }},
  "modus_operandi": "detailed description of the scam technique used",
  "similar_case_patterns": ["list of known similar fraud patterns this matches"],
  "gang_indicators": ["specific indicators suggesting organized gang activity"],
  "suspect_profile": {{
    "likely_organization": "individual | small_gang | organized_crime | state_actor",
    "technical_sophistication": "low | medium | high | very_high",
    "geographic_indicators": "any geographic clues from the case",
    "likely_number_of_suspects": "estimated range",
    "operates_from": "likely state/region if determinable",
    "mule_network_likely": true or false
  }},
  "bns_sections": ["BNS 2023 applicable sections with section numbers AND offense name"],
  "applicable_it_act_sections": ["IT Act sections with section numbers AND offense name"],
  "pmla_sections": ["PMLA sections if money laundering pattern detected, else empty"],
  "other_laws": ["any other applicable acts: BNSS, Consumer Protection Act, etc."],
  "inter_agency_referral": ["RBI | NPCI | DoT | MeitY | ED | CBI | INTERPOL — list relevant agencies"],
  "recommended_immediate_actions": [
    {{"action": "specific action", "who": "officer/bank/agency", "deadline": "time frame"}}
  ]
}}"""

    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
