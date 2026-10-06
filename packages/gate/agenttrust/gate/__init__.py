"""Consequential-action gate. Rule IDs live in rules.py."""

from agenttrust.gate.attach import attach_email, attach_payment
from agenttrust.gate.decide import Intent, chain_for_decision, decide
from agenttrust.gate.rules import (
    AT_DEL_001,
    AT_DEP_001,
    AT_MAIL_001,
    AT_PAY_001,
    AT_PAY_002,
)

__all__ = [
    "AT_DEL_001",
    "AT_DEP_001",
    "AT_MAIL_001",
    "AT_PAY_001",
    "AT_PAY_002",
    "Intent",
    "attach_email",
    "attach_payment",
    "chain_for_decision",
    "decide",
]
