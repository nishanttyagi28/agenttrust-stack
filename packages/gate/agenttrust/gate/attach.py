"""Attach a KarmaSakshi seal and witness. Cryptography stays in that package."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agenttrust.evidence import (
    Chain,
    DecisionOutcome,
    EffectRef,
    EffectType,
    Witness,
)

from agenttrust.gate.decide import Intent, _event_and_decision, chain_for_decision, decide

SOURCE_ACCOUNT = "acct-priya"
CURRENCY = "INR"
REFERENCE = "refund-8842"
IDEMPOTENCY_KEY = "priya-1500"


def attach_payment(intent: Intent, proposed: Intent, *, chain_id: str) -> Chain:
    """Deny in the gate, or seal and witness the approved payment with KarmaSakshi.

    A mismatched attempt never reaches ``engine.commit``. The allow path uses
    ``KarmaSakshiEngine.prepare``, ``seal``, ``authorize``, ``commit``, and
    ``verify`` from ``karmasakshi-protocol``. This module does not hash or
    sign manifests itself.
    """
    if intent.effect_type != EffectType.payment_transfer:
        raise ValueError("attach_payment only seals payment.transfer")
    outcome, rule_id, reason = decide(intent, proposed)
    if outcome != DecisionOutcome.allow:
        return chain_for_decision(intent, proposed, chain_id=chain_id)
    event, decision = _event_and_decision(
        proposed,
        chain_id=chain_id,
        actor_id="refund-agent",
        outcome=outcome,
        rule_id=rule_id,
        reason=reason,
    )
    sealed, proof, adapter_id = _seal_and_witness(intent)
    effect_id = f"{chain_id}-effect"
    witness_id = f"{chain_id}-witness"
    effect = EffectRef(
        id=effect_id,
        caused_by=decision.id,
        manifest_hash=sealed.seal.manifest_hash,
        effect_type=EffectType.payment_transfer,
        adapter_id=adapter_id,
        target_resource=sealed.manifest.target_resource,
    )
    witness = Witness(
        id=witness_id,
        caused_by=effect_id,
        matched_expected=bool(proof.matched_expected),
        adapter_id=adapter_id,
        detail=proof.detail,
    )
    return Chain(
        schema_version="1.0",
        chain_id=chain_id,
        event=event,
        decision=decision,
        effect_ref=effect,
        witness=witness,
        eval_case=None,
    )


def _seal_and_witness(intent: Intent):
    from karmasakshi.adapters.payment_simulator import (
        PaymentRequest,
        PaymentSimulator,
        PaymentSimulatorAdapter,
    )
    from karmasakshi.audit.journal import AuditJournal
    from karmasakshi.config.clock import FixedClock
    from karmasakshi.crypto.keyring import Keyring
    from karmasakshi.crypto.keys import generate_signing_key
    from karmasakshi.domain.common import Principal
    from karmasakshi.domain.enums import PrincipalType
    from karmasakshi.engine.context import EngineContext
    from karmasakshi.engine.core import KarmaSakshiEngine
    from karmasakshi.grants.model import ScopeConstraints
    from karmasakshi.stores.memory import InMemoryGrantStore

    now = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
    clock = FixedClock(now)
    signing_key = generate_signing_key("finance-approver")
    keyring = Keyring([signing_key.verification_key()])
    engine = KarmaSakshiEngine(
        EngineContext(
            keyring=keyring,
            grant_store=InMemoryGrantStore(),
            audit=AuditJournal(clock=clock),
            clock=clock,
        )
    )
    agent = Principal(principal_id="refund-agent", principal_type=PrincipalType.AGENT)
    human = Principal(principal_id="finance-approver", principal_type=PrincipalType.HUMAN)
    simulator = PaymentSimulator()
    simulator.fund_account(SOURCE_ACCOUNT, 1_000_000)
    adapter = PaymentSimulatorAdapter(simulator)
    request = PaymentRequest(
        actor=agent,
        principal=human,
        source_account=SOURCE_ACCOUNT,
        beneficiary=intent.target,
        amount_minor_units=int(intent.amount_minor or 0),
        currency=CURRENCY,
        reference=REFERENCE,
        idempotency_key=IDEMPOTENCY_KEY,
    )
    manifest = engine.prepare(adapter, request, context=None)
    sealed = engine.seal(manifest, signing_key)
    grant = engine.authorize(
        sealed,
        issuer=human,
        subject=agent,
        audience=(adapter.adapter_id,),
        allowed_effect_types=(sealed.manifest.effect_type,),
        scope=ScopeConstraints(),
        not_before=now,
        expires_at=now + timedelta(minutes=5),
        signing_key=signing_key,
    )
    result = engine.commit(sealed, grant, adapter, context=None)
    proof = engine.verify(sealed.manifest, result, adapter, context=None)
    return sealed, proof, adapter.adapter_id
