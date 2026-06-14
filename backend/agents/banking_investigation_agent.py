from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are a Banking Investigation Agent specializing in financial cybercrime.
You analyze transaction patterns, identify mule accounts, trace money laundering chains,
and generate actionable freeze requests for law enforcement.
You understand Indian banking systems: IMPS, NEFT, RTGS, UPI, and digital wallets.
You work within legal frameworks - your freeze requests require human officer approval under:
- Section 318 BNS 2023 (formerly IPC 420)
- Section 66D IT Act 2000
- Section 106 of Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 (formerly Section 102 of CrPC) for order of seizure / freezing.
- Section 94 of BNSS 2023 (formerly Section 91 of CrPC) for calling for documents/transaction logs.
You align with the RBI, NPCI, and Ministry of Home Affairs (MHA) Citizen Financial Cyber Frauds Reporting & Management System (CIBMS) guidelines."""

async def investigate_banking(case_id: str, entities: dict, fraud_analysis: dict, complaint_text: str) -> dict:
    """Analyze banking and transaction aspects of the fraud."""
    
    user_msg = f"""Perform banking investigation for Case {case_id}:

ENTITIES: {entities}
FRAUD ANALYSIS: {fraud_analysis}
COMPLAINT: {complaint_text}

Return JSON:
{{
  "transaction_analysis": {{
    "total_amount_traced": "amount in INR",
    "transaction_chain": [
      {{
        "step": 1,
        "from": "victim account/description",
        "to": "account/UPI ID",
        "amount": "amount",
        "method": "UPI/IMPS/etc",
        "timestamp": "approximate time",
        "is_mule_account": true or false,
        "account_type": "victim | mule_layer_1 | mule_layer_2 | final_beneficiary | crypto_exchange"
      }}
    ],
    "layering_detected": true or false,
    "num_accounts_involved": <number>
  }},
  "freeze_recommendations": [
    {{
      "account_or_upi": "account number or UPI ID",
      "bank_name": "bank name if identifiable",
      "reason": "detailed reason for freeze",
      "priority": "immediate | urgent | standard",
      "estimated_balance": "unknown or estimated amount",
      "freeze_type": "full | partial",
      "legal_basis": "BNSS 2023 Section 106 (formerly CrPC 102) / BNS 318"
    }}
  ],
  "telecom_data_requests": [
    {{
      "number": "phone number",
      "data_needed": "CDR | Tower Dump | Subscriber Details | All",
      "reason": "why this data is needed",
      "priority": "immediate | urgent | standard"
    }}
  ],
  "bank_portal_actions": [
    {{
      "action": "CIBMS freeze | RBI reporting | Bank SPOC alert",
      "target": "bank/account",
      "reason": "reason"
    }}
  ],
  "recovery_strategy": {{
    "immediate_actions": ["list of actions to take in next 24 hours"],
    "week_actions": ["list of actions in first week"],
    "recovery_probability_percentage": <0-100>,
    "key_bottlenecks": ["what might prevent recovery"]
  }}
}}"""

    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result

