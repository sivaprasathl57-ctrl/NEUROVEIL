from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are a Risk Prediction and Anomaly Detection Agent for cybercrime investigation.
You calculate fraud probability, evidence confidence, urgency scores, and predict investigation outcomes.
You identify anomalies in behavior, transactions, and communication patterns.
Your risk scores directly influence how urgently officers prioritize cases."""

async def predict_risk(case_id: str, all_analysis: dict) -> dict:
    """Generate comprehensive risk assessment and predictions."""
    
    user_msg = f"""Generate complete risk assessment for Case {case_id}:

ALL INVESTIGATION DATA: {all_analysis}

Return JSON:
{{
  "overall_scores": {{
    "fraud_probability": <0-100>,
    "evidence_strength": <0-100>,
    "urgency_score": <0-100>,
    "recovery_probability": <0-100>,
    "network_risk": <0-100>
  }},
  "score_justifications": {{
    "fraud_probability_reason": "why this score",
    "urgency_reason": "why urgent or not",
    "recovery_reason": "why recovery is likely or not"
  }},
  "anomalies_detected": [
    {{
      "anomaly": "description of anomaly",
      "type": "behavioral | financial | technical | temporal",
      "significance": "high | medium | low",
      "what_it_means": "investigative significance"
    }}
  ],
  "timeline_reconstruction": [
    {{
      "timestamp": "approximate date/time or relative (e.g. Day 1 10:00 AM)",
      "event": "what happened",
      "actor": "victim | suspect | system",
      "significance": "normal | suspicious | critical"
    }}
  ],
  "predictions": {{
    "case_complexity": "simple | moderate | complex | very_complex",
    "estimated_investigation_days": <number>,
    "likelihood_of_arrest": "high | medium | low | very_low",
    "linked_cases_likely": true or false,
    "cross_state_operation": true or false,
    "international_nexus": true or false
  }},
  "priority_actions": [
    {{
      "action": "specific action to take",
      "who": "cyber_officer | bank | telecom | court | SFIO | ED | Interpol",
      "deadline": "immediate (24hr) | urgent (72hr) | standard (7days)",
      "reason": "why this action is critical"
    }}
  ],
  "alert_type": "none | standard | high_risk | critical | scam_network_alert"
}}"""

    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
