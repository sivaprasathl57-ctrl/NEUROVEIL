"""
PREDICTIVE RISK & ANOMALY DETECTION ENGINE
Advanced ML-style predictive scoring, future threat forecasting, and anomaly detection.
"""

from core.ai_client import call_claude_json
from datetime import datetime, timedelta

SYSTEM_PROMPT = """You are an Advanced Predictive Risk Scoring and ML Anomaly Detection Engine.
Your role is to:
- Score future risk of crime escalation
- Predict victim vulnerability
- Detect behavioral anomalies
- Forecast financial losses
- Identify early warning signs
- Recommend preventive actions

Think like a data scientist combining statistics + cybersecurity."""


async def predict_escalation_risk(case_id: str, case_data: dict, suspect_profile: dict) -> dict:
    """Predict if suspect will escalate to more serious crimes."""
    
    user_msg = f"""Predict escalation risk for case {case_id}:

Current Crime Level: {case_data.get('complaint_analysis', {}).get('scam_type')}
Suspect Profile: {suspect_profile}
Financial Gain So Far: ₹{case_data.get('amount_lost')}
Operational Lifespan: {case_data.get('operational_age', 'Unknown')}
Prior Arrests/Enforcement: {case_data.get('prior_enforcement', 'Unknown')}

Return JSON:
{{
  "escalation_risk_score": <0-100>,
  "escalation_timeline": "within 1 month | 1-3 months | 3-6 months | 6+ months | no escalation likely",
  "predicted_escalation_types": [
    {{
      "escalation": "type of crime escalation",
      "probability": <0-100>,
      "example": "specific example"
    }}
  ],
  "violence_risk": <0-100>,
  "organized_crime_connections": true or false,
  "international_nexus_likelihood": <0-100>,
  "early_warning_signs": [
    "behavioral indicator to watch for",
    "operational change that signals escalation"
  ],
  "recommended_interventions": [
    {{
      "intervention": "specific action",
      "timing": "when to implement",
      "effectiveness": <0-100>
    }}
  ]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def detect_anomalies(case_id: str, case_data: dict, historical_patterns: dict) -> dict:
    """Detect unusual patterns that deviate from normal behavior."""
    
    user_msg = f"""Detect anomalies in case {case_id} compared to historical patterns:

Current Case: {case_data}
Historical Average Transaction: ₹{historical_patterns.get('avg_amount', 'Unknown')}
Typical Victim Profile: {historical_patterns.get('typical_victim', 'Unknown')}
Normal Timeframe: {historical_patterns.get('typical_timeframe', 'Unknown')}

Return JSON:
{{
  "anomaly_detected": true or false,
  "anomalies": [
    {{
      "anomaly": "specific deviation from pattern",
      "severity": "low | medium | high | critical",
      "deviation_percentage": <0-200>,
      "implication": "what this might indicate"
    }}
  ],
  "novelty_score": <0-100>,
  "threat_level_adjustment": "normal | elevated | high | critical",
  "potential_new_threat": "is this a new attack pattern?",
  "recommendations": ["action items"]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def forecast_victim_vulnerability(victim_profile: dict) -> dict:
    """Score how vulnerable a person is to future scams."""
    
    user_msg = f"""Score cyber-scam vulnerability for victim profile:

Profile: {victim_profile}

Assess vulnerabilities across multiple dimensions and return JSON:
{{
  "overall_vulnerability_score": <0-100>,
  "vulnerability_dimensions": {{
    "technical_literacy": <0-100>,
    "trust_propensity": <0-100>,
    "financial_decision_making": <0-100>,
    "emotional_intelligence": <0-100>,
    "verification_habits": <0-100>
  }},
  "high_risk_scam_types": [
    {{
      "scam_type": "type victim is vulnerable to",
      "risk_score": <0-100>,
      "reason": "why this victim vulnerable"
    }}
  ],
  "protective_factors": ["strengths that protect victim"],
  "risk_factors": ["weaknesses that increase vulnerability"],
  "recommendations": [
    "specific protective actions victim should take",
    "educational content needed"
  ]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def forecast_financial_impact(case_data: dict, all_cases: dict) -> dict:
    """Forecast total potential financial impact if criminal continues."""
    
    user_msg = f"""Forecast financial impact if this criminal pattern continues:

Initial Case Loss: ₹{case_data.get('amount_lost')}
Scam Type: {case_data.get('complaint_analysis', {}).get('scam_type')}
Sophistication: {case_data.get('fraud_classification', {}).get('suspect_profile', {}).get('technical_sophistication')}
Operational Efficiency: {case_data.get('operational_efficiency', 'Unknown')}
Growth Pattern: {case_data.get('growth_pattern', 'Unknown')}

Return JSON:
{{
  "base_loss": <amount>,
  "projected_monthly_victims": <number>,
  "projected_average_per_victim": <amount>,
  "annual_forecast": {{
    "if_unchecked_12_months": <total amount>,
    "if_with_intervention": <estimated reduction>,
    "confidence": <0-100>
  }},
  "escalation_scenarios": [
    {{
      "scenario": "description",
      "probability": <0-100>,
      "annual_impact": <amount>
    }}
  ],
  "intervention_roi": "if we stop this now, loss prevented",
  "urgency_level": "immediate action required | high priority | standard"
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
