"""The lane map is an invariant, so it gets tested like one."""

from __future__ import annotations

from tools.check_allowlist import ACTOR_ROLES, AGENTS, NON_ACTOR_ROLES, allowed


def test_sprint_roles_are_not_actors() -> None:
    """p0..p4 span packages by design; if they counted as actors the guard would
    always pass and GOVERNANCE.md would be lying."""
    assert NON_ACTOR_ROLES.isdisjoint(ACTOR_ROLES)
    assert set(ACTOR_ROLES) | set(NON_ACTOR_ROLES) == set(AGENTS)


def test_no_actor_owns_both_the_schema_and_the_check() -> None:
    """The whole point of lanes: an agent must not be able to rewrite the thing
    and the test of the thing in one diff (see POSTMORTEMS/0001)."""
    for role in ACTOR_ROLES:
        patterns = AGENTS[role]
        owns_schema = allowed("packages/evidence/agenttrust/evidence/models.py", patterns)
        owns_check = allowed("packages/ci/agenttrust/ci/check.py", patterns)
        assert not (owns_schema and owns_check), (
            f"{role} owns both the evidence schema and the CI check"
        )


def test_governance_is_a_real_lane() -> None:
    assert "governance" in ACTOR_ROLES
    for path in ("GOVERNANCE.md", "POSTMORTEMS/0001-unsigned-evidence-chain.md", ".githooks/pre-commit"):
        assert allowed(path, AGENTS["governance"]), path


def test_evidence_lane_cannot_reach_the_check() -> None:
    assert allowed("tests/evidence/test_signing.py", AGENTS["evidence"])
    assert not allowed("packages/ci/agenttrust/ci/check.py", AGENTS["evidence"])


def test_gate_lane_cannot_reach_the_schema() -> None:
    assert allowed("packages/ci/agenttrust/ci/check.py", AGENTS["gate"])
    assert not allowed("packages/evidence/agenttrust/evidence/models.py", AGENTS["gate"])


def test_glob_semantics_for_directory_patterns() -> None:
    assert allowed("docs/adopt.md", AGENTS["p4"])
    assert not allowed("docs/adopt.md", AGENTS["gate"])
    assert allowed("examples/ci-drop-in/agenttrust.yml", AGENTS["p4"])
