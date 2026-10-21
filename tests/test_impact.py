import shutil
from pathlib import Path

import pytest

from reasoner import impact
from reasoner.kb import KB_DIR, load_kb

from .helpers import cs_claim, make_claim


@pytest.fixture
def edited_kb(tmp_path):
    copy = tmp_path / "kb"
    shutil.copytree(KB_DIR, copy)
    return copy


def weaken_preauth(directory: Path) -> None:
    rule = directory / "rules" / "r3_preauth.metta"
    rule.write_text(rule.read_text().replace("(stv 0.95 0.92)", "(stv 0.5 0.92)"))


def test_an_unchanged_rulebook_has_no_impact():
    kb = load_kb()
    assert impact.compare([cs_claim()], kb, kb) == []


def test_a_changed_truth_value_is_reported_with_the_claims_it_moves(edited_kb):
    weaken_preauth(edited_kb)
    claims = [cs_claim(), make_claim(claim_ref="clm-fine", patient_token="pat-1")]
    changes = impact.compare(claims, load_kb(KB_DIR), load_kb(edited_kb))
    assert [change.claim_ref for change in changes] == ["clm-104"]
    assert changes[0].before.verdict == "WILL_FAIL" and changes[0].after.verdict == "AT_RISK"
    text = impact.render(changes, 2, load_kb(KB_DIR), load_kb(edited_kb))
    assert "clm-104" in text and "WILL_FAIL → AT_RISK" in text and "2 synthetic claims" in text


def test_a_rule_edit_without_a_version_bump_is_stale(edited_kb):
    weaken_preauth(edited_kb)
    assert impact.version_is_stale(KB_DIR, edited_kb)
    (edited_kb / "VERSION").write_text("sha-rules-9999\n")
    assert not impact.version_is_stale(KB_DIR, edited_kb)


def test_documentation_changes_do_not_need_a_bump(edited_kb):
    (edited_kb / "rules" / "truth-values.md").write_text("reworded")
    (edited_kb / "LICENSE").write_text("reworded")
    assert not impact.version_is_stale(KB_DIR, edited_kb)


def test_identical_rulebooks_share_a_fingerprint(edited_kb):
    assert impact.behaviour_fingerprint(KB_DIR) == impact.behaviour_fingerprint(edited_kb)
