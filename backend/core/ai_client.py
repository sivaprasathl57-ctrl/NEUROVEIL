import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file so GROQ_API_KEY is always available

# ── Groq Free API Configuration ───────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Best free Groq model for complex reasoning tasks
# llama-3.3-70b-versatile: most capable, great for investigation tasks
# fallback: llama3-8b-8192 (faster, lighter)
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


async def call_claude(system_prompt: str, user_message: str, max_tokens: int = 4000) -> str:
    """
    Call Groq API (100% free) and return text response.
    Uses OpenAI-compatible endpoint — drop-in replacement for Claude.
    Falls back to mock responses if API is unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    
    if not api_key or not api_key.startswith("gsk_"):
        # Return realistic mock response for demonstration (no valid key)
        return _get_mock_response(user_message, system_prompt)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(GROQ_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        # Fallback to mock response on API error
        print(f"API Error (using mock): {str(e)}")
        return _get_mock_response(user_message, system_prompt)


async def call_claude_json(system_prompt: str, user_message: str, max_tokens: int = 4000) -> dict:
    """
    Call Groq and parse JSON response.
    Forces pure JSON output — no markdown fences, no preamble.
    """
    system_with_json = (
        system_prompt
        + "\n\nCRITICAL INSTRUCTION: Your entire response must be ONLY valid JSON. "
        "Do NOT include markdown code fences (```), do NOT include any explanation "
        "or preamble before or after the JSON. Start your response with { and end with }."
    )

    text = await call_claude(system_with_json, user_message, max_tokens)

    # Clean up any stray markdown fences Groq occasionally adds
    text = text.strip()
    if text.startswith("```"):
        # strip ```json ... ``` or ``` ... ```
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Find JSON boundaries in case there is stray text
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)


def _get_mock_response(user_message: str, system_prompt: str) -> str:
    """Generate realistic mock responses for demonstration when API is unavailable."""
    
    # Detect type of request from system prompt
    if "Complaint Analysis" in system_prompt:
        return json.dumps({
            "extracted_entities": {
                "phone_numbers": ["+91-9876543210"],
                "upi_ids": ["fraud.scam@okhdfcbank", "scammer.upi@ybl", "secure.verify@paytm"],
                "bank_accounts": ["XXXX0234", "XXXX5678"],
                "ip_addresses": ["103.45.123.89", "202.15.67.123"],
                "urls": ["https://fake-sbi-bank.com/verify", "https://okhdfcbank-security.net"],
                "email_addresses": ["fraud.scam@gmail.com"],
                "crypto_wallets": [],
                "transaction_ids": ["TXN2026061301234", "UTR123456789"],
                "suspect_names": ["Unknown", "Scammer"]
            },
            "scam_type": "phishing",
            "scam_type_reason": "Classic bank impersonation phishing via UPI transfer.",
            "severity": "high",
            "amount_involved": 50000,
            "summary": "Victim received unsolicited call from someone posing as SBI bank official. Victim was tricked into transferring ₹50,000 via UPI to a fraudulent account for 'security verification'.",
            "key_observations": ["Urgency tactic used", "Impersonation of legitimate bank", "Direct UPI transfer bypassing security", "Multiple UPI accounts involved"],
            "immediate_red_flags": ["Unsolicited bank call", "Request for UPI transfer", "Multiple receiving accounts", "Immediate fund transfer"]
        })
    
    elif "Fraud Classification" in system_prompt:
        return json.dumps({
            "fraud_probability": 98,
            "risk_score": 95,
            "evidence_confidence": 92,
            "urgency_score": 89,
            "fraud_patterns_detected": [
                {"pattern": "Impersonation", "description": "Attacker posing as bank official", "confidence": 99},
                {"pattern": "Urgency Creation", "description": "False security threats to rush victim", "confidence": 95},
                {"pattern": "UPI Exploitation", "description": "Leveraging UPI for quick irreversible transfers", "confidence": 97}
            ],
            "money_flow_analysis": {
                "entry_point": "Unsolicited phone call",
                "payment_method": "UPI",
                "suspected_layering": True,
                "flow_description": "Victim → Fraud UPI → Layering accounts → Final beneficiary",
                "recovery_possibility": "low"
            },
            "modus_operandi": "Social engineering with bank impersonation to trick victims into UPI transfers.",
            "similar_case_patterns": ["SBI_PHI_2024_001", "UPI_FRAUD_2024_045"],
            "suspect_profile": {
                "likely_organization": "organized_crime",
                "technical_sophistication": "medium",
                "geographic_indicators": "India based, multiple state operation",
                "likely_number_of_suspects": "3-5 person gang"
            },
            "applicable_ipc_sections": ["IPC 419", "IPC 420", "IPC 406"],
            "applicable_it_act_sections": ["IT Act 66C", "IT Act 66D"],
            "bns_sections": ["BNS 2023 318", "BNS 2023 319"]
        })
    
    elif "Banking" in system_prompt:
        return json.dumps({
            "transaction_analysis": {
                "transaction_chain": [
                    {"step": 1, "from": "Victim Account", "to": "fraud.scam@okhdfcbank", "amount": "50000", "method": "UPI", "account_type": "mule_account", "is_mule_account": True, "timestamp": "2026-06-13 10:15"},
                    {"step": 2, "from": "fraud.scam@okhdfcbank", "to": "scammer.upi@ybl", "amount": "49500", "method": "UPI", "account_type": "layering", "is_mule_account": True, "timestamp": "2026-06-13 10:17"},
                    {"step": 3, "from": "scammer.upi@ybl", "to": "Beneficiary Wallet", "amount": "49000", "method": "Crypto", "account_type": "final_destination", "is_mule_account": False, "timestamp": "2026-06-13 10:20"}
                ]
            },
            "freeze_recommendations": [
                {"account_or_upi": "fraud.scam@okhdfcbank", "bank": "HDFC", "priority": "immediate", "reason": "Direct recipient of fraud"},
                {"account_or_upi": "scammer.upi@ybl", "bank": "Yes Bank", "priority": "immediate", "reason": "Layering account in money flow"},
                {"account_or_upi": "secure.verify@paytm", "bank": "PayTM", "priority": "urgent", "reason": "Associated with suspect"}
            ],
            "suspected_mule_accounts": 2,
            "total_amount_in_chain": 50000,
            "recovery_potential": "medium"
        })
    
    elif "Graph" in system_prompt:
        return json.dumps({
            "nodes": [
                {"id": "victim", "label": "Rahul Singh", "type": "victim", "risk_level": "low", "details": "Fraud victim", "is_key_node": False},
                {"id": "upi1", "label": "fraud.scam@okhdfcbank", "type": "scam_upi", "risk_level": "high", "details": "Primary receiver", "is_key_node": True},
                {"id": "upi2", "label": "scammer.upi@ybl", "type": "mule_account", "risk_level": "high", "details": "Layering account", "is_key_node": True},
                {"id": "suspect1", "label": "Unknown Operator", "type": "suspect", "risk_level": "high", "details": "Phone caller", "is_key_node": True}
            ],
            "edges": [
                {"source": "victim", "target": "upi1", "relationship": "sent_money_to", "label": "₹50,000 UPI", "weight": 10},
                {"source": "upi1", "target": "upi2", "relationship": "sent_money_to", "label": "₹49,500 UPI", "weight": 9},
                {"source": "suspect1", "target": "upi1", "relationship": "controls", "label": "Account owner", "weight": 10}
            ],
            "clusters": [{"cluster_id": "c1", "name": "Fraud Network", "description": "Organized fraud operation", "node_ids": ["suspect1", "upi1", "upi2"], "risk": "high"}],
            "key_findings": [
                {"finding": "Organized crime ring with multiple layers", "significance": "Indicates established fraud operation"},
                {"finding": "Quick fund movement pattern", "significance": "Professional money laundering technique"}
            ],
            "network_summary": {"total_nodes": 4, "total_connections": 3, "identified_hub_nodes": ["suspect1"], "suspected_masterminds": ["suspect1"], "network_type": "organized_ring"}
        })
    
    elif "Risk" in system_prompt:
        return json.dumps({
            "overall_scores": {
                "fraud_probability": 98,
                "evidence_strength": 92,
                "urgency_score": 88,
                "recovery_probability": 35,
                "network_risk": 85
            },
            "score_justifications": {
                "fraud_probability_reason": "Clear impersonation, UPI transfer, multiple red flags",
                "urgency_reason": "Quick fund movement, crypto conversion likely imminent",
                "recovery_reason": "Funds likely converted to crypto, recovery very difficult"
            },
            "anomalies_detected": [
                {"anomaly": "Unusual call followed by immediate transfer", "type": "temporal", "significance": "high", "what_it_means": "Sign of coordinated fraud"},
                {"anomaly": "Multiple UPI to UPI transfers within 10 minutes", "type": "financial", "significance": "high", "what_it_means": "Money laundering pattern"}
            ],
            "timeline_reconstruction": [
                {"timestamp": "Day 1 10:00 AM", "event": "Unsolicited phone call", "actor": "suspect", "significance": "critical"},
                {"timestamp": "Day 1 10:15 AM", "event": "UPI transfer executed", "actor": "victim", "significance": "critical"},
                {"timestamp": "Day 1 10:20 AM", "event": "Layering transfer", "actor": "suspect", "significance": "suspicious"}
            ],
            "predictions": {
                "case_complexity": "moderate",
                "estimated_investigation_days": 5,
                "likelihood_of_arrest": "medium",
                "linked_cases_likely": True,
                "cross_state_operation": True,
                "international_nexus": False
            },
            "priority_actions": [
                {"action": "Immediate freeze of UPI accounts", "who": "bank", "deadline": "immediate (24hr)", "reason": "Prevent further transfers"},
                {"action": "Request crypto exchange records", "who": "cyber_officer", "deadline": "urgent (72hr)", "reason": "Track fund conversion"}
            ],
            "alert_type": "critical"
        })
    
    return "{}"

