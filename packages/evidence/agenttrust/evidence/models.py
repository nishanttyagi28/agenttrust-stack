"""Evidence Schema v1 Pydantic models."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

RULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(-[A-Z0-9]+)+$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SCHEMA_VERSION = "1.0"


class DecisionOutcome(str, Enum):
    allow = "allow"
    deny = "deny"
    unknown = "unknown"


class EffectType(str, Enum):
    payment_transfer = "payment.transfer"
    email_send = "email.send"
    data_delete = "data.delete"
    deploy_release = "deploy.release"


class ApprovalState(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


def _require_non_empty(value: str, field_name: str) -> str:
    if not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _validate_json_object(value: dict[str, Any], field_name: str) -> dict[str, Any]:
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{field_name} keys must be strings")
        _validate_json_value(item, field_name)
    return value


def _validate_json_value(value: Any, field_name: str) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        raise ValueError(f"{field_name} must not contain lists")
    if isinstance(value, dict):
        _validate_json_object(value, field_name)
        return
    raise ValueError(f"{field_name} contains a non-JSON value type: {type(value).__name__}")


class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: ApprovalState
    actor: str | None
    note: str | None


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    caused_by: str | None
    actor_id: str
    timestamp: str
    action_type: str
    payload: dict[str, Any]

    @field_validator("id", "actor_id", "action_type")
    @classmethod
    def _non_empty_strings(cls, value: str, info) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: str) -> str:
        if not TIMESTAMP_RE.match(value):
            raise ValueError(
                "timestamp must match YYYY-MM-DDTHH:MM:SSZ (UTC, no fractional seconds)"
            )
        return value

    @field_validator("payload")
    @classmethod
    def _validate_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_json_object(value, "payload")


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    caused_by: str
    outcome: DecisionOutcome
    rule_id: str | None
    policy_version: str | None
    reason: str | None

    @field_validator("id", "caused_by")
    @classmethod
    def _non_empty_strings(cls, value: str, info) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("rule_id")
    @classmethod
    def _validate_rule_id_format(cls, value: str | None) -> str | None:
        if value is not None and not RULE_ID_RE.match(value):
            raise ValueError(
                f"rule_id must match {RULE_ID_RE.pattern!r} when present"
            )
        return value


class EffectRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    caused_by: str
    manifest_hash: str
    effect_type: EffectType
    adapter_id: str
    target_resource: str

    @field_validator("id", "caused_by", "manifest_hash", "adapter_id", "target_resource")
    @classmethod
    def _non_empty_strings(cls, value: str, info) -> str:
        return _require_non_empty(value, info.field_name)


class Witness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    caused_by: str
    matched_expected: bool | None
    adapter_id: str
    detail: str | None

    @field_validator("id", "caused_by", "adapter_id")
    @classmethod
    def _non_empty_strings(cls, value: str, info) -> str:
        return _require_non_empty(value, info.field_name)


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    caused_by: str
    chain_id: str
    case_id: str
    prompt: str
    expects: dict[str, Any]
    approval: Approval

    @field_validator("id", "caused_by", "chain_id", "case_id", "prompt")
    @classmethod
    def _non_empty_strings(cls, value: str, info) -> str:
        return _require_non_empty(value, info.field_name)

    @field_validator("expects")
    @classmethod
    def _validate_expects(cls, value: dict[str, Any]) -> dict[str, Any]:
        return _validate_json_object(value, "expects")


class Chain(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    chain_id: str
    event: Event
    decision: Decision
    effect_ref: EffectRef | None
    witness: Witness | None
    eval_case: EvalCase | None

    @field_validator("chain_id")
    @classmethod
    def _non_empty_chain_id(cls, value: str) -> str:
        return _require_non_empty(value, "chain_id")

    @model_validator(mode="after")
    def _validate_chain(self) -> Chain:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f'schema_version must be exactly "{SCHEMA_VERSION}"')

        if self.event.caused_by is not None:
            raise ValueError("event.caused_by must be null")

        if self.decision.caused_by != self.event.id:
            raise ValueError("decision.caused_by must equal event.id")

        record_ids: list[str] = [
            self.event.id,
            self.decision.id,
        ]
        if self.effect_ref is not None:
            record_ids.append(self.effect_ref.id)
        if self.witness is not None:
            record_ids.append(self.witness.id)
        if self.eval_case is not None:
            record_ids.append(self.eval_case.id)

        for record_id in record_ids:
            if not record_id:
                raise ValueError("all record ids must be non-empty")

        if len(record_ids) != len(set(record_ids)):
            raise ValueError("all record ids in the chain must be unique")

        outcome = self.decision.outcome

        if self.decision.rule_id is not None and not RULE_ID_RE.match(self.decision.rule_id):
            raise ValueError(
                f"rule_id must match {RULE_ID_RE.pattern!r} when present"
            )

        if outcome == DecisionOutcome.deny and self.decision.rule_id is None:
            raise ValueError("rule_id is required when outcome is deny")

        if outcome in (DecisionOutcome.deny, DecisionOutcome.unknown):
            if self.effect_ref is not None:
                raise ValueError("effect_ref must be null when outcome is deny or unknown")
            if self.witness is not None:
                raise ValueError("witness must be null when outcome is deny or unknown")
            if self.eval_case is not None:
                if self.eval_case.caused_by != self.decision.id:
                    raise ValueError(
                        "eval_case.caused_by must equal decision.id when outcome is deny or unknown"
                    )
                if self.eval_case.chain_id != self.chain_id:
                    raise ValueError("eval_case.chain_id must equal chain.chain_id")

        if outcome == DecisionOutcome.allow:
            if self.effect_ref is None:
                raise ValueError("effect_ref is required when outcome is allow")
            if self.witness is None:
                raise ValueError("witness is required when outcome is allow")
            if self.effect_ref.caused_by != self.decision.id:
                raise ValueError("effect_ref.caused_by must equal decision.id")
            if self.witness.caused_by != self.effect_ref.id:
                raise ValueError("witness.caused_by must equal effect_ref.id")
            if self.eval_case is not None:
                if self.eval_case.caused_by != self.witness.id:
                    raise ValueError(
                        "eval_case.caused_by must equal witness.id when outcome is allow"
                    )
                if self.eval_case.chain_id != self.chain_id:
                    raise ValueError("eval_case.chain_id must equal chain.chain_id")

        return self
