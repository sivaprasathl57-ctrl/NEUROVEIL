"""
BLOCKCHAIN INTELLIGENCE & CRYPTO FORENSICS ENGINE
Traces cryptocurrency transactions, identifies mixers, detects DeFi scams,
maps wallet networks, and generates blockchain IOCs.
"""

from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are a Blockchain Forensics and Cryptocurrency Intelligence Expert.
Your capabilities:
- Bitcoin/Ethereum transaction tracing
- Mixer detection (Tornado Cash, ChipMixer, etc.)
- Wallet clustering and ownership inference
- DeFi scam identification
- Rug pull detection
- Wallet heat mapping
- Money laundering pattern recognition
- Cross-chain bridge tracking

Analyze crypto cases with precision and generate blockchain-specific IOCs."""


async def trace_crypto_transactions(case_id: str, wallet_addresses: list, case_data: dict) -> dict:
    """Trace cryptocurrency transactions and money flow."""
    
    user_msg = f"""Trace cryptocurrency transactions for case {case_id}:

Wallet Addresses to Investigate: {wallet_addresses}
Initial Amount: ₹{case_data.get('amount_lost')} (INR equivalent)
Scam Type: {case_data.get('complaint_analysis', {}).get('scam_type')}
Suspected Crypto: Bitcoin | Ethereum | USDT | Other

Analyze blockchain data (simulated for authorized forensics) and return JSON:
{{
  "transaction_trace": [
    {{
      "transaction_hash": "txid",
      "timestamp": "ISO timestamp",
      "from_address": "sending address",
      "to_address": "receiving address",
      "amount": "crypto amount",
      "usd_equivalent": "dollar value",
      "confirmations": "number of blockchain confirms",
      "risk_indicators": ["list of suspicious indicators"]
    }}
  ],
  "wallet_analysis": [
    {{
      "address": "wallet address",
      "estimated_owner": "profiling of likely owner",
      "total_inflow": "total crypto received",
      "total_outflow": "total sent out",
      "age": "how long active",
      "activity_pattern": "when used, frequency",
      "mixer_usage": true or false,
      "exchange_connections": "known exchanges this wallet interacts with",
      "risk_score": <0-100>
    }}
  ],
  "money_flow_path": {{
    "entry_point": "where crypto was initially deposited",
    "layering_steps": ["intermediate wallets used for mixing"],
    "exit_point": "where money was eventually cashed out",
    "total_hops": "number of transfers",
    "estimated_laundering_success": <0-100>
  }},
  "mixer_detection": {{
    "mixers_used": ["list of identified mixers"],
    "mixing_efficiency": "how well mixed",
    "re-identification_difficulty": "easy | medium | hard | nearly_impossible"
  }},
  "defi_scam_indicators": [
    "list of DeFi red flags if applicable",
    "rug pull indicators",
    "fake token patterns"
  ],
  "blockchain_iocs": {{
    "addresses_to_monitor": wallet_addresses,
    "associated_exchanges": ["exchanges linked to wallets"],
    "flagged_patterns": ["patterns for law enforcement"]
  }},
  "recovery_feasibility": {{
    "recovery_probability": <0-100>,
    "freeze_timeframe": "window to freeze before exit",
    "exchange_contact": "which exchange likely involved",
    "recommended_action": "specific law enforcement action"
  }}
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result


async def analyze_defi_scam(case_id: str, case_data: dict) -> dict:
    """Analyze DeFi-specific fraud patterns."""
    
    user_msg = f"""Analyze potential DeFi scam elements in case {case_id}:

Case Type: {case_data.get('complaint_analysis', {}).get('scam_type')}
Narrative: {case_data.get('complaint_text')}
Suspect Wallets: {case_data.get('complaint_analysis', {}).get('extracted_entities', {}).get('crypto_wallets', [])}

Return JSON:
{{
  "defi_elements_detected": true or false,
  "scam_type": "rug_pull | fake_token | flash_loan | liquidity_trap | yield_farming_scam | bridge_exploit",
  "indicators": [
    {{
      "indicator": "specific red flag",
      "severity": "low | medium | high | critical",
      "explanation": "why this is suspicious"
    }}
  ],
  "smart_contract_analysis": {{
    "contract_address": "token contract address if known",
    "deployment_date": "when launched",
    "owner_actions": ["suspicious owner functions"],
    "liquidity_lock": "is liquidity locked?",
    "mint_function": "can creator create unlimited tokens?",
    "backdoor_functions": ["hidden malicious functions"]
  }},
  "victim_loss_mechanism": "how victims actually lose money",
  "perpetrator_profit_model": "how scammer profits",
  "spread_pattern": "how victims were recruited",
  "estimated_total_victims": <number>,
  "law_enforcement_report": "formatted for police filing"
}}"""
    
    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
