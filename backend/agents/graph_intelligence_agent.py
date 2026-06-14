from core.ai_client import call_claude_json

SYSTEM_PROMPT = """You are a Graph Intelligence Agent that builds criminal network relationship graphs.
You map connections between victims, scam accounts, mule accounts, devices, phone numbers,
and crypto wallets. You identify clusters, key nodes (hubs), and reveal organized crime networks.
Your output is used to visualize fraud networks and find the masterminds behind operations."""

async def build_fraud_graph(case_id: str, entities: dict, banking_data: dict, fraud_data: dict) -> dict:
    """Build the fraud relationship graph."""
    
    user_msg = f"""Build a fraud intelligence graph for Case {case_id}:

ENTITIES: {entities}
BANKING ANALYSIS: {banking_data}
FRAUD ANALYSIS: {fraud_data}

Return JSON for network graph visualization:
{{
  "nodes": [
    {{
      "id": "unique_id",
      "label": "display name",
      "type": "victim | scam_upi | mule_account | phone_number | ip_address | crypto_wallet | suspect | device | url | email",
      "risk_level": "high | medium | low",
      "details": "brief description",
      "is_key_node": true or false
    }}
  ],
  "edges": [
    {{
      "source": "node_id",
      "target": "node_id",
      "relationship": "sent_money_to | registered_with | called | accessed_from | controls | linked_to | same_device",
      "label": "edge label",
      "weight": <1-10>
    }}
  ],
  "clusters": [
    {{
      "cluster_id": "cluster_1",
      "name": "cluster name",
      "description": "what this cluster represents",
      "node_ids": ["list of node ids in this cluster"],
      "risk": "high | medium | low"
    }}
  ],
  "key_findings": [
    {{
      "finding": "important finding from graph analysis",
      "significance": "why this matters for investigation"
    }}
  ],
  "network_summary": {{
    "total_nodes": <number>,
    "total_connections": <number>,
    "identified_hub_nodes": ["nodes that connect many others"],
    "suspected_masterminds": ["high-risk key nodes"],
    "network_type": "isolated | small_network | organized_ring | large_syndicate"
  }}
}}"""

    result = await call_claude_json(SYSTEM_PROMPT, user_msg)
    return result
