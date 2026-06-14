"""
ADVANCED IOC GENERATION & THREAT INTELLIGENCE EXPORT
Generates court-ready IOCs, exportable threat intelligence, and law enforcement-shareable formats.
Supports multiple standards: STIX, MISP, CSV, JSON, PDF.
"""

from core.ai_client import call_claude_json
import json
from datetime import datetime

SYSTEM_PROMPT = """You are an Expert Threat Intelligence IOC Generation Specialist.
Generate actionable Indicators of Compromise across all IOC types:
- IP addresses, domains, URLs, email addresses
- File hashes, behavioral signatures
- Phone numbers, bank accounts, UPI IDs
- Crypto wallets, device identifiers
- Command & control patterns
- Malware signatures

Format for law enforcement, FBI, Interpol, and cybersecurity tools."""


async def generate_advanced_iocs(case_id: str, investigation_data: dict) -> dict:
    """Generate comprehensive IOCs for law enforcement and threat intelligence sharing."""
    
    user_msg = f"""Generate complete IOC package for case {case_id}:

Investigation Data: {investigation_data}

Return comprehensive JSON:
{{
  "ioc_metadata": {{
    "case_id": "{case_id}",
    "generated_date": "{datetime.now().isoformat()}",
    "confidence_level": <0-100>,
    "severity": "critical | high | medium | low",
    "sharing_restriction": "white | green | amber | red"
  }},
  "network_indicators": {{
    "ip_addresses": [
      {{
        "ip": "1.2.3.4",
        "type": "attacker | proxy | c2 | infrastructure",
        "confidence": <0-100>,
        "related_to": "description",
        "first_seen": "date",
        "last_seen": "date"
      }}
    ],
    "domains": [
      {{
        "domain": "attacker.com",
        "type": "c2 | phishing | fake_banking",
        "ip_resolves_to": ["list of IPs"],
        "whois_holder": "registrant info",
        "ssl_certificate": "certificate hash",
        "confidence": <0-100>
      }}
    ],
    "urls": [
      {{
        "url": "https://phishing.site/login",
        "type": "phishing | malware_download | c2",
        "first_seen": "date",
        "response_code": <status>,
        "content_hash": "sha256 hash",
        "confidence": <0-100>
      }}
    ]
  }},
  "financial_indicators": {{
    "upi_ids": [
      {{
        "upi": "fraud@okhdfcbank",
        "bank": "HDFC",
        "account_holder": "inference",
        "risk_level": "high",
        "total_fraud_amount": <total>
      }}
    ],
    "bank_accounts": [
      {{
        "ifsc": "SBIN0001234",
        "account_last_4": "5678",
        "holder_name": "if known",
        "transactions_flagged": <count>
      }}
    ],
    "crypto_wallets": [
      {{
        "address": "1A1z7agoat...",
        "blockchain": "Bitcoin | Ethereum",
        "total_received": <amount>,
        "mixer_usage": true or false,
        "risk_score": <0-100>
      }}
    ]
  }},
  "communication_indicators": {{
    "phone_numbers": [
      {{
        "number": "+91-XXXXXXXXXX",
        "country_code": "IN",
        "simcard_type": "prepaid | postpaid",
        "associated_accounts": ["UPI, bank, etc"],
        "confidence": <0-100>
      }}
    ],
    "email_addresses": [
      {{
        "email": "attacker@email.com",
        "platform": "gmail | outlook | custom",
        "creation_date": "estimate",
        "associated_accounts": ["linked services"]
      }}
    ]
  }},
  "device_indicators": {{
    "device_fingerprints": [
      {{
        "fingerprint_type": "browser | device | hardware",
        "identifier": "hash or ID",
        "associated_cases": ["list of cases"]
      }}
    ],
    "behavioral_signatures": [
      {{
        "behavior": "pattern description",
        "confidence": <0-100>,
        "detection_method": "how identified"
      }}
    ]
  }},
  "malware_indicators": {{
    "file_hashes": ["md5, sha1, sha256 if malware involved"],
    "c2_communications": ["command & control patterns"],
    "exploit_techniques": ["CVE numbers, techniques used"],
    "signatures": ["YARA rules if applicable"]
  }},
  "attack_pattern": {{
    "tactics": ["list of MITRE ATT&CK tactics"],
    "techniques": ["specific MITRE ATT&CK techniques"],
    "procedure": "step-by-step attack flow"
  }},
  "export_formats": {{
    "stix_bundle": "STIX 2.1 format for automated ingestion",
    "misp_event": "MISP format for threat intelligence platforms",
    "csv_iocs": "comma-separated IOC list",
    "yara_rules": "YARA detection rules if applicable",
    "pdf_report": "formatted PDF for law enforcement"
  }},
  "law_enforcement_data": {{
    "fir_applicable_sections": ["IPC sections", "IT Act", "BNS sections"],
    "evidence_summary": "courtroom-ready summary",
    "recommended_action": "specific law enforcement steps",
    "inter_agency_coordination": ["agencies to involve"]
  }},
  "sharing_guidelines": {{
    "approved_recipients": ["law enforcement agencies, cybersecurity firms"],
    "classified_level": "if any data is sensitive",
    "export_restriction": "legal considerations"
  }}
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def generate_threat_report(case_id: str, investigation_data: dict) -> dict:
    """Generate executive threat intelligence report."""
    
    user_msg = f"""Generate an executive threat intelligence report for case {case_id}:

Investigation: {investigation_data}

Return JSON:
{{
  "title": "Threat Intelligence Report - Case {case_id}",
  "executive_summary": "2-3 paragraph overview",
  "threat_level": "critical | high | medium | low",
  "affected_sector": "financial | healthcare | retail | government | other",
  "threat_actor": {{
    "name": "assigned threat actor name",
    "sophistication": "script kiddie | advanced | APT",
    "motivation": "financial | espionage | ideology",
    "geolocation": "likely country/region"
  }},
  "attack_overview": "detailed description",
  "timeline": [
    {{
      "date": "when attack occurred",
      "event": "what happened"
    }}
  ],
  "impact_assessment": {{
    "victims_affected": <number>,
    "financial_loss": <amount>,
    "data_compromised": "what data stolen if any",
    "business_disruption": "operational impact"
  }},
  "indicators_of_compromise": ["list of IOCs"],
  "recommendations": [
    {{
      "priority": "critical | high | medium",
      "action": "specific recommendation",
      "timeline": "when to implement"
    }}
  ],
  "references": ["sources of information"],
  "distribution": "intended distribution (public | law enforcement | specific sectors)"
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
