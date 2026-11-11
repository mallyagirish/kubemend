"""Per-rule tests: every rule fires on its vulnerable fixture, and (except
guidance-only KM005) its fix makes the finding go away."""

import os

import pytest

from kubemend_engine import fix_file, scan_path

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
AUTO_FIXABLE = ["KM001", "KM002", "KM003", "KM004", "KM006", "KM007", "KM008", "KM009", "KM010"]


def _ids(findings):
    return {f.rule_id for f in findings}


@pytest.mark.parametrize("rule_id", AUTO_FIXABLE + ["KM005"])
def test_rule_fires_on_vulnerable_fixture(rule_id):
    findings = scan_path(os.path.join(FIXTURES, rule_id, "vulnerable.yaml"))
    assert rule_id in _ids(findings)


@pytest.mark.parametrize("rule_id", AUTO_FIXABLE)
def test_fix_resolves_finding(rule_id, tmp_path):
    source = os.path.join(FIXTURES, rule_id, "vulnerable.yaml")
    _original, patched, fixed = fix_file(source)
    assert any(f.rule_id == rule_id for f in fixed)
    target = tmp_path / "patched.yaml"
    target.write_text(patched)
    assert rule_id not in _ids(scan_path(str(target)))


def test_km005_is_guidance_only():
    """KM005 must never fabricate a digest: it reports, it does not patch."""
    findings = scan_path(os.path.join(FIXTURES, "KM005", "vulnerable.yaml"))
    km005 = [f for f in findings if f.rule_id == "KM005"]
    assert km005 and km005[0].fix_description is None
    assert "sha256" in km005[0].explanation


def test_fixed_fixtures_scan_clean():
    for rule_id in AUTO_FIXABLE + ["KM005"]:
        findings = scan_path(os.path.join(FIXTURES, rule_id, "fixed.yaml"))
        assert findings == [], f"{rule_id}/fixed.yaml should be clean, got {_ids(findings)}"


def test_findings_cite_field_paths():
    findings = scan_path(os.path.join(FIXTURES, "KM001", "vulnerable.yaml"))
    km001 = [f for f in findings if f.rule_id == "KM001"][0]
    assert km001.field_path == "spec.template.spec.containers[0].resources.requests"
    assert km001.resource == "Deployment/default/demo"
    assert km001.container == "app"
