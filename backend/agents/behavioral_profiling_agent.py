"""
ADVANCED BEHAVIORAL PROFILING ENGINE
AI-driven psychological and behavioral analysis of cyber criminals.
Predicts next moves, identifies psychological triggers, builds suspect profiles.
"""

from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are an Advanced Criminal Behavioral Profiling AI.
Your expertise spans:
- Cybercriminal psychology
- Social engineering tactics
- Financial crime patterns
- Risk-taking behavior analysis
- Psychological motivation assessment
- Addiction patterns in scammers
- Organizational hierarchy prediction in crime rings

Analyze cases like a profiler combining data science + psychology."""


async def profile_suspect_behavior(case_id: str, case_data: dict, investigation_data: dict) -> dict:
    """Generate advanced behavioral profile of suspected criminal."""
    
    user_msg = f"""Build a detailed behavioral profile for the suspect(s) in case {case_id}:

CASE DATA:
- Scam Type: {case_data.get('complaint_analysis', {}).get('scam_type')}
- Amount Targeted: ₹{case_data.get('amount_lost')}
- Communication Style: {investigation_data.get('communication_pattern', 'Unknown')}
- Victim Selection: {investigation_data.get('victim_profile', 'Unknown')}
- Technical Sophistication: {investigation_data.get('fraud_classification', {}).get('suspect_profile', {}).get('technical_sophistication')}
- Modus Operandi: {investigation_data.get('fraud_classification', {}).get('modus_operandi')}
- Operational Hours: {investigation_data.get('operational_pattern', 'Unknown')}
- Adaptation Pattern: {investigation_data.get('adaptation_level', 'Unknown')}

Return JSON:
{{
  "psychological_profile": {{
    "personality_type": "narcissistic | sociopathic | opportunistic | professional | ideological",
    "motivation": "financial_gain | thrill_seeking | revenge | addiction | ideology",
    "risk_tolerance": "very_low | low | medium | high | extreme",
    "impulsivity_score": <0-100>,
    "planning_sophistication": "chaotic | basic | structured | highly_organized"
  }},
  "operational_behavior": {{
    "work_pattern": "single_operator | small_gang | organized_ring | enterprise",
    "decision_making": "impulsive | calculated | adaptive | rigid",
    "victim_targeting": "random | deliberate | social_network | demographic_specific",
    "communication_style": "aggressive | manipulative | friendly | official_sounding",
    "failure_response": "abandons_method | doubles_down | adapts_quickly | blames_others"
  }},
  "predicted_psychology": {{
    "likely_background": "estimated socioeconomic, education, technical background",
    "probable_age_range": "estimated age bracket",
    "geographic_origin": "likely country/region based on patterns",
    "internet_addiction_indicators": true or false,
    "signs_of_mental_health": "description if any",
    "likelihood_of_escalation": "to violence | to larger schemes | to recruitment"
  }},
  "prediction_engine": {{
    "next_likely_move": "predicted next step",
    "target_profile": "description of likely next victim",
    "timeline": "when next attack likely",
    "escalation_risk": "will this person become more dangerous?"
  }},
  "counter_psychology": [
    {{
      "strategy": "specific intervention approach",
      "reason": "why this works against this psychological type",
      "likelihood_of_success": <0-100>
    }}
  ],
  "rehabilitation_assessment": {{
    "likelihood_of_reform": <0-100>,
    "required_interventions": ["list of interventions"],
    "risk_of_recidivism": <0-100>
  }}
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def predict_next_move(case_id: str, investigation_data: dict) -> dict:
    """Predict the suspect's next move based on behavioral analysis."""
    
    user_msg = f"""Based on the investigation for case {case_id}, predict what the suspect will do next:

Suspect Profile: {investigation_data.get('suspect_profile', {})}
Previous Tactics: {investigation_data.get('modus_operandi', '')}
Operational Constraints: {investigation_data.get('operational_constraints', '')}
Success Rate: {investigation_data.get('success_rate', 'Unknown')}

Return JSON:
{{
  "predictions": [
    {{
      "scenario": "specific predicted action",
      "probability": <0-100>,
      "timeline": "when likely",
      "target_profile": "who will be targeted",
      "financial_amount": "expected fraud value",
      "detection_difficulty": "easy | medium | hard | very_hard"
    }}
  ],
  "counter_measures": [
    {{
      "measure": "specific action to prevent predicted move",
      "implementation": "how to deploy",
      "effectiveness": <0-100>
    }}
  ],
  "pattern_shift_indicators": [
    "signs the suspect will change tactics",
    "behavioral red flags to watch for"
  ]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
