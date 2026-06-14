"""
ADVANCED MULTI-CASE CORRELATION ENGINE
Links multiple cases, identifies serial criminals, detects coordinated fraud rings.
"""

from core.ai_client import call_claude_json
from typing import List, Dict

SYSTEM_PROMPT = """You are an Advanced Multi-Case Correlation Intelligence Engine.
Your role is to analyze multiple cybercrime cases and identify:
1. Serial criminals (same suspect operating multiple cases)
2. Coordinated fraud rings (organized groups)
3. Attack pattern similarities (same modus operandi)
4. Victim networks (same circles targeted)
5. Money flow patterns (connected financial trails)
6. Shared infrastructure (same IPs, domains, bank accounts)

Think like a detective connecting case files to build a complete criminal network map."""


async def correlate_multiple_cases(case_ids: List[str], cases_data: Dict[str, dict]) -> dict:
    """Correlate multiple cases to find hidden connections."""
    
    # Prepare case summaries
    case_summaries = []
    for case_id in case_ids:
        if case_id in cases_data:
            case = cases_data[case_id]
            case_summaries.append({
                "case_id": case_id,
                "scam_type": case.get("complaint_analysis", {}).get("scam_type", "Unknown"),
                "amount": case.get("amount_lost", "0"),
                "victim": case.get("victim_name", "Unknown"),
                "upi_ids": case.get("complaint_analysis", {}).get("extracted_entities", {}).get("upi_ids", []),
                "phone_numbers": case.get("complaint_analysis", {}).get("extracted_entities", {}).get("phone_numbers", []),
                "fraud_prob": case.get("fraud_classification", {}).get("fraud_probability", 0),
            })
    
    user_msg = f"""Analyze these {len(case_summaries)} cybercrime cases and find correlations:

{case_summaries}

Return JSON:
{{
  "total_cases_analyzed": {len(case_summaries)},
  "correlation_groups": [
    {{
      "group_id": "RING-001",
      "type": "organized_ring | serial_criminal | copycat_network",
      "case_ids": ["list of linked case IDs"],
      "confidence": <0-100>,
      "suspected_size": "1-2 | 3-5 | 5-10 | 10+ members",
      "shared_indicators": {{
        "upi_ids": ["common UPI accounts used"],
        "phone_numbers": ["linked phone numbers"],
        "domains": ["shared infrastructure"],
        "attack_pattern": "detailed modus operandi"
      }},
      "estimated_total_loss": <amount>,
      "danger_level": "low | medium | high | critical"
    }}
  ],
  "serial_criminal_profiles": [
    {{
      "profile_id": "SUSPECT-001",
      "linked_cases": ["case IDs"],
      "estimated_role": "mastermind | executor | money_mule | recruiter",
      "skill_level": "novice | intermediate | expert | advanced",
      "likely_location": "India | International | Unknown",
      "threat_assessment": "Profile analysis"
    }}
  ],
  "network_graph": {{
    "suspects": ["list of suspect profiles"],
    "victims": ["patterns in victim selection"],
    "money_flow": "description of financial connections"
  }},
  "recommendations": [
    {{
      "action": "specific law enforcement action",
      "priority": "immediate | urgent | standard",
      "reason": "why this action matters"
    }}
  ]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def identify_serial_criminal(case_id: str, case_data: dict, all_cases: Dict[str, dict]) -> dict:
    """Check if a case belongs to a known serial criminal."""
    
    user_msg = f"""This case (ID: {case_id}) shows these characteristics:

Victim: {case_data.get('victim_name')}
Amount Lost: ₹{case_data.get('amount_lost')}
Scam Type: {case_data.get('complaint_analysis', {}).get('scam_type')}
UPI IDs Used: {case_data.get('complaint_analysis', {}).get('extracted_entities', {}).get('upi_ids', [])}
Phone Numbers: {case_data.get('complaint_analysis', {}).get('extracted_entities', {}).get('phone_numbers', [])}

Check against {len(all_cases)} other cases in database.

Return JSON:
{{
  "is_serial_criminal": true or false,
  "confidence": <0-100>,
  "linked_cases": ["case_ids of other cases by same criminal"],
  "suspect_profile": {{
    "estimated_experience": "novice | experienced | expert",
    "targeting_strategy": "random | targeted | personal_networks",
    "technical_skill": "low | medium | high",
    "psychological_profile": "analysis of attacker behavior"
  }},
  "predicted_next_target": "profile of likely next victim",
  "counter_measures": ["specific actions to stop this criminal"]
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
