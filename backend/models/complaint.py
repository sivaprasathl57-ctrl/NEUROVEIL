from dataclasses import dataclass
from typing import Optional


@dataclass
class ComplaintRequest:
    complaint_text: str
    victim_name: str
    victim_contact: str
    transaction_ids: Optional[str] = ""
    upi_ids: Optional[str] = ""
    urls: Optional[str] = ""
    amount_lost: Optional[str] = "0"


@dataclass
class HumanApprovalRequest:
    decision: str
    officer_notes: Optional[str] = ""
